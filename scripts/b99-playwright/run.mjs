import assert from "node:assert/strict";
import { readFileSync, mkdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";
import { chromium, expect } from "@playwright/test";

const base = "http://127.0.0.1:4173";
const backendLog = process.env.B99_BACKEND_LOG || "/tmp/b99-backend.log";
const seed = JSON.parse(readFileSync("/tmp/turnoment-b99-browser-seed.json", "utf8"));
const artifacts = "artifacts/b99-real-browser";
mkdirSync(artifacts, { recursive: true });

async function otpFor(phone) {
  for (let attempt = 0; attempt < 100; attempt++) {
    let log = "";
    try { log = readFileSync(backendLog, "utf8"); } catch {}
    const matches = [...log.matchAll(/\[turnoment-local-otp\] phone=(\+\d+) code=(\d{6})/g)]
      .filter((match) => match[1] === phone);
    if (matches.length) return matches.at(-1)[2];
    await delay(100);
  }
  throw new Error("Local disposable OTP was not delivered for a browser session");
}

async function login(page, phone) {
  await page.goto(base + "/login?redirect=%2Fdashboard%2Fchallenges");
  await expect(page.getByRole("heading", { name: "ورود با کد یکبارمصرف" })).toBeVisible();
  await page.locator("#login-phone").fill(phone.replace(/^\+98/, "0"));
  const otpHttp = page.waitForResponse(
    (response) => response.url().includes("/api/v1/auth/otp/request/"),
    { timeout: 15000 },
  ).catch(() => null);
  await page.getByRole("button", { name: "دریافت کد ورود" }).click();
  const sentResponse = await otpHttp;
  console.log("B99 OTP POST HTTP status:", sentResponse?.status() ?? "NO NETWORK RESPONSE");
  try {
    await expect(
      page.getByText("کد ورود ارسال شد. کد ۶ رقمی را وارد کن."),
    ).toBeVisible({ timeout: 8000 });
  } catch (error) {
    console.error("B99 OTP UI feedback:", await page.locator("#login-feedback").innerText());
    console.error("B99 current browser URL:", page.url());
    if (sentResponse) {
      const payload = await sentResponse.json().catch(() => null);
      console.error("B99 OTP HTTP error code:",
        payload?.error?.code ?? "(no error code)");
    }
    throw error;
  }
  const otp = await otpFor(phone);
  await page.locator('input[autocomplete="one-time-code"]').fill(otp);
  await page.getByRole("button", { name: "تأیید و ورود" }).click();
  await page.waitForURL(/\/dashboard\/challenges/, { timeout: 30000 });
  await expect(page.getByRole("heading", { name: "چالش‌های من" })).toBeVisible();
  const me = await readJson(page, "/api/v1/auth/me/");
  assert.equal(me.status, 200);
  return me.payload.id;
}

async function readJson(page, path) {
  return page.evaluate(async (endpoint) => {
    const result = await fetch(endpoint, { credentials: "include" });
    return { status: result.status, payload: await result.json().catch(() => null) };
  }, path);
}

async function writeJson(page, endpoint, body, key, withCsrf = true) {
  return page.evaluate(async (args) => {
    let token;
    if (args.withCsrf) {
      const bootstrap = await fetch("/api/v1/auth/csrf/", { credentials: "include" });
      if (!bootstrap.ok) throw new Error("CSRF bootstrap failed: " + bootstrap.status);
      token = (await bootstrap.json()).csrf_token;
    }
    const response = await fetch(args.endpoint, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(token ? { "X-CSRFToken": token } : {}),
        ...(args.key ? { "Idempotency-Key": args.key } : {}),
      },
      body: JSON.stringify(args.body),
    });
    return { status: response.status, payload: await response.json().catch(() => null) };
  }, { endpoint, body, key, withCsrf });
}

function backendCommand(code) {
  const result = spawnSync("python", ["manage.py", "shell", "-c", code], {
    encoding: "utf8",
    env: { ...process.env, DJANGO_SETTINGS_MODULE: "config.settings.local" },
  });
  assert.equal(result.status, 0, "Backend operator step failed: " + result.stderr);
  return result.stdout;
}

const browser = await chromium.launch({ headless: true });
const contextA = await browser.newContext();
const contextB = await browser.newContext();
const contextThird = await browser.newContext();
const a = await contextA.newPage();
const b = await contextB.newPage();
const third = await contextThird.newPage();
const pageErrors = [];
for (const page of [a, b, third]) {
  page.on("pageerror", (error) => pageErrors.push(error.message));
}

try {
  const aId = await login(a, seed.phones.alpha);
  const bId = await login(b, seed.phones.bravo);
  const strangerId = await login(third, seed.phones.third);
  assert.equal(new Set([aId, bId, strangerId]).size, 3);
  const sessionCookie = async (ctx) => (await ctx.cookies(base))
    .find((cookie) => cookie.name === "turnoment_sessionid")?.value;
  const sessions = await Promise.all([contextA, contextB, contextThird].map(sessionCookie));
  assert(sessions.every(Boolean), "All browsers must have real Django sessions");
  assert.equal(new Set(sessions).size, 3, "Browser cookies must not be shared");

  await expect(a.getByText("بخش چالش فعال است")).toBeVisible();
  await a.getByRole("button", { name: "ایجاد چالش جدید" }).click();
  const dialog = a.getByRole("dialog");
  await dialog.locator("#challenge-opponent-search").fill("b99webbravo");
  await dialog.getByRole("button", { name: "جست‌وجو", exact: true }).click();
  await expect(dialog.getByRole("radio", { name: /b99webbravo/i })).toBeVisible();
  await dialog.getByRole("radio", { name: /b99webbravo/i }).click();
  await dialog.getByRole("button", { name: "ارسال دعوت چالش" }).click();
  await expect(a.getByText("دعوت چالش ثبت شد.")).toBeVisible();

  await b.reload();
  await expect(b.getByRole("button", { name: "پذیرفتن چالش" })).toBeVisible();
  const challengeAcceptResponses = [];
  const recordChallengeAccept = (response) => {
    const path = new URL(response.url()).pathname;
    if (path.startsWith("/api/v1/challenges/")) {
      challengeAcceptResponses.push({ method: response.request().method(), path, status: response.status() });
    }
  };
  b.on("response", recordChallengeAccept);
  try {
    await b.getByRole("button", { name: "پذیرفتن چالش" }).click();
    await expect(b.getByText("دعوت چالش پذیرفته شد.")).toBeVisible();
  } catch (error) {
    console.error("B99 challenge accept response metadata:", JSON.stringify(challengeAcceptResponses));
    console.error("B99 challenge accept status/alert text:",
      JSON.stringify(await b.locator('[role="status"], [role="alert"]').allInnerTexts().catch(() => [])));
    console.error("B99 challenge accept URL:", b.url());
    throw error;
  } finally {
    b.off("response", recordChallengeAccept);
  }

  const matchesA = await readJson(a, "/api/v1/me/matches/");
  const matchesB = await readJson(b, "/api/v1/me/matches/");
  assert.equal(matchesA.status, 200);
  assert.equal(matchesB.status, 200);
  const challengeMatchesA = matchesA.payload.items.filter(
    (item) => item.competition.kind === "challenge",
  );
  const challengeMatchesB = matchesB.payload.items.filter(
    (item) => item.competition.kind === "challenge",
  );
  assert.equal(challengeMatchesA.length, 1);
  assert.equal(challengeMatchesB.length, 1);
  const matchId = challengeMatchesA[0].matchId;
  assert.equal(challengeMatchesB[0].matchId, matchId);

  const deniedRead = await readJson(third, "/api/v1/matches/" + matchId + "/result/");
  assert.equal(deniedRead.status, 404, "Outsider must not read a private result");
  // A separate authenticated user must not mutate the private result or
  // access/open a dispute, even with a valid CSRF token and command shape.
  const outsiderResultWrite = await writeJson(
    third, "/api/v1/matches/" + matchId + "/result/",
    { revision: "0", playerScore: 4, opponentScore: 2 },
    "b99-browser-outsider-result",
  );
  assert.equal(outsiderResultWrite.status, 404, "Outsider must not submit a result");
  const disputeEndpoint = "/api/v1/matches/" + matchId + "/dispute/";
  const outsiderDisputeRead = await readJson(third, disputeEndpoint);
  assert.equal(outsiderDisputeRead.status, 404, "Outsider must not read a dispute");
  const outsiderDisputeWrite = await writeJson(
    third, disputeEndpoint,
    {
      revision: "0", reason: "incorrect-score",
      statement: "This match is private and I am not a participant.",
    },
    "b99-browser-outsider-dispute",
  );
  assert.equal(outsiderDisputeWrite.status, 404, "Outsider must not open a dispute");
  const deniedDashboard = await readJson(third, "/api/v1/me/dashboard/");
  assert.equal(deniedDashboard.status, 200);
  assert.equal(deniedDashboard.payload.snapshot.finalizedMatches, 0);

  // The source/operator only makes the scheduled challenge match ready.
  // Both real start/finish transitions must be driven through the React UI.
  backendCommand(
    "from apps.matches.services import advance_match; " +
    "advance_match('" + matchId + "', 'ready')",
  );
  const readyMatches = await readJson(a, "/api/v1/me/matches/");
  assert.equal(readyMatches.status, 200);
  const readyMatch = readyMatches.payload.items.find((item) => item.matchId === matchId);
  assert(readyMatch, "Accepted challenge must appear in the player's match list");
  assert.equal(readyMatch.lifecycleState, "ready");
  assert.equal(readyMatch.canControlLifecycle, true);
  const lifecycleEndpoint = "/api/v1/matches/" + matchId + "/lifecycle/";
  const outsiderLifecycle = await writeJson(third, lifecycleEndpoint, {
    command: "start", revision: readyMatch.revision,
  });
  assert.equal(outsiderLifecycle.status, 404,
    "Outsider must not start a participant's challenge match");

  const matchesNavigation = await a.goto(base + "/dashboard/matches");
  try {
    await expect(a.getByRole("heading", { name: "Matchهای من" })).toBeVisible();
  } catch (error) {
    const matchList = await readJson(a, "/api/v1/me/matches/").catch(() => null);
    const first = matchList?.payload?.items?.[0];
    console.error("B99 lifecycle UI navigation diagnostics:", JSON.stringify({
      navigationStatus: matchesNavigation?.status() ?? null,
      finalUrl: a.url(),
      title: await a.title().catch(() => null),
      headingsAndAlerts: await a.locator("h1,h2,[role=alert],[role=status]")
        .allInnerTexts().catch(() => []),
      matchListStatus: matchList?.status ?? null,
      matchListKeys: matchList?.payload ? Object.keys(matchList.payload) : [],
      firstMatchKeys: first ? Object.keys(first) : [],
      firstMatchState: first?.lifecycleState ?? null,
      firstMatchResultState: first?.resultState ?? null,
      pageErrors,
    }));
    await a.screenshot({
      path: artifacts + "/lifecycle-ui-navigation-failure.png", fullPage: true,
    }).catch(() => null);
    console.error("B99 lifecycle UI API contract values:", JSON.stringify({
      player: matchList?.payload?.player ?? null,
      summary: matchList?.payload?.summary ?? null,
      pagination: matchList?.payload?.pagination ?? null,
      firstMatch: first ?? null,
    }));
    const parsedContract = await a.evaluate(async () => {
      try {
        const module = await import("/src/lib/my-matches-http-repository.ts");
        const data = await new module.ApiMyMatchesRepository().getMyMatches({
          state: "all", kind: "all", page: 1,
        });
        return { valid: true, items: data.items.length };
      } catch (caught) {
        return {
          valid: false,
          error: String(caught),
          issues: Array.isArray(caught?.issues)
            ? caught.issues.map((issue) => ({
                path: issue.path, code: issue.code, message: issue.message,
              })).slice(0, 20)
            : [],
        };
      }
    }).catch((caught) => ({ valid: false, moduleError: String(caught) }));
    console.error("B99 lifecycle frontend contract parser diagnostics:",
      JSON.stringify(parsedContract));
    try {
      await a.goto(base + "/dashboard/challenges");
      await expect(a.getByRole("heading", { name: "چالش‌های من" })).toBeVisible();
      await a.getByRole("link", { name: "Matchهای من" }).first().click();
      await a.waitForTimeout(1500);
      console.error("B99 lifecycle client-navigation comparison:", JSON.stringify({
        finalUrl: a.url(),
        headingsAndAlerts: await a.locator("h1,h2,[role=alert],[role=status]")
          .allInnerTexts().catch(() => []),
        pageErrors,
      }));
    } catch (navigationError) {
      console.error("B99 lifecycle client-navigation diagnostic failed:",
        String(navigationError));
    }
    throw error;
  }
  // Keep the acceptance assertion unchanged. On failure, record only
  // method/path/status and UI state; never log cookies, CSRF values or PII.
  const lifecycleNetwork = [];
  const recordLifecycleRequest = (request) => {
    const path = new URL(request.url()).pathname;
    if (path === lifecycleEndpoint || path === "/api/v1/auth/csrf/") {
      lifecycleNetwork.push({ event: "request", method: request.method(), path });
    }
  };
  const recordLifecycleResponse = (response) => {
    const path = new URL(response.url()).pathname;
    if (path === lifecycleEndpoint || path === "/api/v1/auth/csrf/") {
      lifecycleNetwork.push({
        event: "response", method: response.request().method(),
        path, status: response.status(),
      });
    }
  };
  a.on("request", recordLifecycleRequest);
  a.on("response", recordLifecycleResponse);
  const startButton = a.getByRole("button", { name: "شروع بازی" });
  let startResponse;
  try {
    const startHttp = a.waitForResponse((response) =>
      new URL(response.url()).pathname === lifecycleEndpoint &&
      response.request().method() === "POST",
    );
    await startButton.click();
    startResponse = await startHttp;
  } catch (error) {
    const button = await startButton.evaluate((node) => ({
      disabled: node.disabled, busy: node.getAttribute("aria-busy"),
      visible: Boolean(node.getClientRects().length),
    })).catch(() => null);
    const liveList = await readJson(a, "/api/v1/me/matches/").catch(() => null);
    const target = liveList?.payload?.items?.find((item) => item.matchId === matchId);
    // Preflight the exact client-side action adapter without issuing a mutation.
    const actionPreflight = await a.evaluate(async (revision) => {
      try {
        const [actions, adapter] = await Promise.all([
          import("/src/lib/match-actions-repository.ts"),
          import("/src/lib/data-adapter.ts"),
        ]);
        const parsed = actions.lifecycleCommandSchema.safeParse({
          command: "start", revision,
        });
        let apiBaseOrigin = null;
        let baseError = null;
        let csrfRequestStatus = null;
        let csrfRequestError = null;
        try {
          const base = actions.matchActionsRepository.baseUrl?.();
          apiBaseOrigin = base ? new URL(base).origin : null;
          // Safe GET only; never log the CSRF token or send a lifecycle command.
          if (base) {
            try {
              const response = await actions.matchActionsRepository.request(
                new URL("api/v1/auth/csrf/", base),
              );
              csrfRequestStatus = response.status;
            } catch (error) { csrfRequestError = String(error); }
          }
        } catch (error) { baseError = String(error); }
        return {
          adapterMode: adapter.getDataAdapterMode(),
          commandValid: parsed.success,
          commandIssues: parsed.success ? [] : parsed.error.issues.map(
            (issue) => ({ path: issue.path, code: issue.code }),
          ),
          repoClass: actions.matchActionsRepository.constructor.name,
          requestType: typeof actions.matchActionsRepository.request,
          apiBaseOrigin, baseError, csrfRequestStatus, csrfRequestError,
        };
      } catch (error) {
        return { importOrAdapterError: String(error) };
      }
    }, target?.revision).catch((error) => ({ evaluationError: String(error) }));
    console.error("B99 lifecycle start diagnostic:", JSON.stringify({
      expectedPath: lifecycleEndpoint,
      network: lifecycleNetwork,
      actionPreflight,
      button,
      apiStatus: liveList?.status ?? null,
      target: target ? {
        matchId: target.matchId, lifecycleState: target.lifecycleState,
        canControlLifecycle: target.canControlLifecycle,
        hasRevision: Boolean(target.revision),
        revisionLength: String(target.revision ?? "").length,
      } : null,
      feedback: await a.locator('[role="status"],[role="alert"]')
        .allInnerTexts().catch(() => []),
      pageErrors,
    }));
    await a.screenshot({
      path: artifacts + "/lifecycle-start-network-failure.png", fullPage: true,
    }).catch(() => null);
    throw error;
  } finally {
    a.off("request", recordLifecycleRequest);
    a.off("response", recordLifecycleResponse);
  }
  assert.equal(startResponse.status(), 200, "Start must reach the real API");
  const started = await startResponse.json();
  assert.equal(started.outcome, "accepted");
  assert.equal(started.state, "live");

  await expect(a.getByRole("button", {
    name: "بازی تمام شد؛ ثبت نتیجه",
  })).toBeVisible();
  const finishHttp = a.waitForResponse((response) =>
    new URL(response.url()).pathname === lifecycleEndpoint &&
    response.request().method() === "POST",
  );
  await a.getByRole("button", { name: "بازی تمام شد؛ ثبت نتیجه" }).click();
  const finishResponse = await finishHttp;
  assert.equal(finishResponse.status(), 200, "Finish must reach the real API");
  const finished = await finishResponse.json();
  assert.equal(finished.outcome, "accepted");
  assert.equal(finished.state, "awaiting-result");
  const finishedMatchesB = await readJson(b, "/api/v1/me/matches/");
  assert.equal(finishedMatchesB.status, 200);
  assert.equal(finishedMatchesB.payload.items.find(
    (item) => item.matchId === matchId,
  )?.lifecycleState, "awaiting-result");
  console.log("B99 MATCH LIFECYCLE UI PASS: participant start/finish via React, outsider denied");
  const endpoint = "/api/v1/matches/" + matchId + "/result/";
  const resultA = await readJson(a, endpoint);
  assert.equal(resultA.status, 200);
  const deniedCsrf = await writeJson(
    a, endpoint,
    { revision: resultA.payload.revision, playerScore: 4, opponentScore: 2 },
    "b99-browser-no-csrf", false,
  );
  assert.equal(deniedCsrf.status, 403, "Unsafe mutation must require CSRF");
  const submitted = await writeJson(
    a, endpoint,
    { revision: resultA.payload.revision, playerScore: 4, opponentScore: 2 },
    "b99-browser-real-score",
  );
  assert.equal(submitted.status, 200);
  assert.equal(submitted.payload.outcome, "accepted");
  const resultB = await readJson(b, endpoint);
  const confirmed = await writeJson(b, endpoint + "confirm/", {
    revision: resultB.payload.revision, playerScore: 2, opponentScore: 4,
  });
  assert.equal(confirmed.status, 200);
  assert.equal(confirmed.payload.outcome, "finalized");
  const again = await writeJson(b, endpoint + "confirm/", {
    revision: resultB.payload.revision, playerScore: 2, opponentScore: 4,
  });
  assert.equal(again.payload.outcome, "already_finalized");

  const firstDrain = backendCommand(
    "from django.core.management import call_command; " +
    "call_command('drain_b08_events', limit=100)",
  );
  assert.match(firstDrain, /Applied 31 B08 events/);
  const replay = backendCommand(
    "from django.core.management import call_command; " +
    "call_command('drain_b08_events', limit=100)",
  );
  assert.match(replay, /Applied 0 B08 events/);

  const ranks = await readJson(
    a, "/api/v1/rankings/?game=" + seed.gameSlug +
      "&season=" + seed.season + "&type=challenge",
  );
  assert.equal(ranks.status, 200);
  assert.deepEqual(ranks.payload.items.map((x) => x.rating), [1016, 984]);
  assert(!JSON.stringify(ranks.payload).includes("+98912"), "Public rankings leaked phone");

  const dashboardA = await readJson(a, "/api/v1/me/dashboard/");
  const dashboardB = await readJson(b, "/api/v1/me/dashboard/");
  assert.equal(dashboardA.payload.snapshot.challengeRating, 1016);
  assert.equal(dashboardB.payload.snapshot.challengeRating, 984);
  assert.equal(dashboardA.payload.snapshot.finalizedMatches, 31);
  assert.equal(dashboardB.payload.snapshot.finalizedMatches, 31);

  // A second disposable match covers a participant score disagreement and
  // dispute without disturbing the finalized challenge/ranking acceptance above.
  // Its lifecycle is operator-driven; this does NOT certify the dispute UI.
  const disputeSetup = backendCommand(
    "from apps.accounts.models import User; " +
    "from apps.games.models import Game; " +
    "from apps.matches.services import create_match_for_source, advance_match; " +
    "from django.utils import timezone; " +
    "a=User.objects.get(phone=" + JSON.stringify(seed.phones.alpha) + "); " +
    "b=User.objects.get(phone=" + JSON.stringify(seed.phones.bravo) + "); " +
    "g=Game.objects.get(slug=" + JSON.stringify(seed.gameSlug) + "); " +
    "m=create_match_for_source(source_kind='tournament', " +
    "source_id='b99-browser-dispute-1', participant_a=a, participant_b=b, " +
    "game_id=g.pk, game_name=g.name, competition_title='B99 disagreement acceptance', " +
    "starts_at=timezone.now()); " +
    "advance_match(m.pk, 'ready'); advance_match(m.pk, 'awaiting-result'); " +
    "print('B99_DISPUTE_MATCH_ID='+str(m.pk))",
  );
  const disputeMatchId = disputeSetup.match(/B99_DISPUTE_MATCH_ID=([0-9a-f-]{36})/)?.[1];
  assert(disputeMatchId, "Disposable disagreement match was not created");
  const disputeResultEndpoint = "/api/v1/matches/" + disputeMatchId + "/result/";
  const disputeResultA = await readJson(a, disputeResultEndpoint);
  assert.equal(disputeResultA.status, 200);
  const disputeSubmitted = await writeJson(a, disputeResultEndpoint, {
    revision: disputeResultA.payload.revision, playerScore: 4, opponentScore: 2,
  }, "b99-disagreement-result");
  assert.equal(disputeSubmitted.status, 200);
  assert.equal(disputeSubmitted.payload.outcome, "accepted");
  const disputeResultB = await readJson(b, disputeResultEndpoint);
  assert.equal(disputeResultB.status, 200);
  const disagreement = await writeJson(b, disputeResultEndpoint + "confirm/", {
    revision: disputeResultB.payload.revision, playerScore: 3, opponentScore: 4,
  });
  assert.equal(disagreement.status, 200);
  assert.equal(disagreement.payload.outcome, "score_mismatch");
  const disputePath = "/api/v1/matches/" + disputeMatchId + "/dispute/";
  const eligibleDispute = await readJson(b, disputePath);
  assert.equal(eligibleDispute.status, 200);
  assert.equal(eligibleDispute.payload.disputeState, "eligible");
  const disputeCommand = {
    revision: eligibleDispute.payload.revision,
    reason: "incorrect-score",
    statement: "The opponent score was reported incorrectly in this match.",
  };
  const openedDispute = await writeJson(b, disputePath, disputeCommand, "b99-disagreement-open");
  assert.equal(openedDispute.status, 200);
  assert.equal(openedDispute.payload.outcome, "accepted");
  const disputeReplay = await writeJson(b, disputePath, disputeCommand, "b99-disagreement-open");
  assert.equal(disputeReplay.status, 200);
  assert.equal(disputeReplay.payload.outcome, "already_open");
  for (const participant of [a, b]) {
    const visibleDispute = await readJson(participant, disputePath);
    assert.equal(visibleDispute.status, 200);
    assert.equal(visibleDispute.payload.disputeState, "open");
    assert.equal(visibleDispute.payload.result.state, "disputed");
  }
  assert.equal((await readJson(third, disputePath)).status, 404);
  const disputeDrain = backendCommand(
    "from django.core.management import call_command; " +
    "call_command('drain_b08_events', limit=100)",
  );
  assert.match(disputeDrain, /Applied 0 B08 events/,
    "A disputed, unfinalized match must not create a ranking event");
  const rankingAfterDispute = await readJson(
    a, "/api/v1/rankings/?game=" + seed.gameSlug +
      "&season=" + seed.season + "&type=challenge",
  );
  assert.deepEqual(rankingAfterDispute.payload.items.map((x) => x.rating), [1016, 984]);
  console.log("B99 DISPUTE API PASS: score mismatch, participant dispute, replay, " +
    "outsider denial, no premature rating");

  // Real center-admin API permissions: owner may manage the center, staff can
  // read only permitted venue data, and an unrelated player has no access.
  // Fixture is restricted to the disposable local PostgreSQL E2E database.
  const centerSetup = backendCommand(
    "from apps.accounts.models import User; " +
    "from apps.gaming_centers.models import City, GamingCenter, CenterMembership; " +
    "c=GamingCenter.objects.create(public_id='b99-browser-center', " +
    "name='B99 Browser Center', city=City.objects.get(slug='b99-karaj'), " +
    "district='QA', summary='Disposable center for browser permission checks.', " +
    "description='Temporary gaming center used only in the isolated B99 PostgreSQL acceptance database.'); " +
    "CenterMembership.objects.create(center=c, " +
    "user=User.objects.get(phone=" + JSON.stringify(seed.phones.alpha) + "), " +
    "role=CenterMembership.Role.OWNER); " +
    "CenterMembership.objects.create(center=c, " +
    "user=User.objects.get(phone=" + JSON.stringify(seed.phones.bravo) + "), " +
    "role=CenterMembership.Role.STAFF); " +
    "print('B99_CENTER_ID='+str(c.pk))",
  );
  const centerId = centerSetup.match(/B99_CENTER_ID=([0-9a-f-]{36})/)?.[1];
  assert(centerId, "Disposable center was not created");
  const centerApi = "/api/v1/center-admin/centers/" + centerId + "/";
  assert.equal((await readJson(a, centerApi)).status, 200,
    "Center owner must read own center");
  assert.equal((await readJson(b, centerApi)).status, 200,
    "Active center staff must read own center");
  assert.equal((await readJson(third, centerApi)).status, 403,
    "Unrelated player must not read private center admin data");
  assert.equal((await readJson(a, centerApi + "staff/")).status, 200);
  assert.equal((await readJson(b, centerApi + "staff/")).status, 403,
    "Center staff must not enumerate memberships");
  assert.equal((await readJson(third, centerApi + "staff/")).status, 403);
  const equipment = { label: "B99 Disposable PC", isPublic: false };
  assert.equal((await writeJson(b, centerApi + "equipment/", equipment)).status, 403,
    "Center staff must not mutate equipment");
  assert.equal((await writeJson(third, centerApi + "equipment/", equipment)).status, 403,
    "Unrelated player must not mutate equipment");
  assert.equal((await writeJson(a, centerApi + "equipment/", equipment)).status, 201,
    "Center owner must be allowed to manage equipment");
  const ownerEquipment = await readJson(a, centerApi + "equipment/");
  assert.equal(ownerEquipment.status, 200);
  assert.equal(ownerEquipment.payload.items.length, 1);
  assert.equal((await readJson(third, centerApi + "equipment/")).status, 403);
  console.log("B99 CENTER ADMIN API PASS: owner write, staff read-only, outsider denied");

  // A third disposable match validates the actual dispute form in API mode.
  // Operator setup remains isolated to the CI PostgreSQL database; player B
  // submits the dispute through the rendered browser UI, not a direct fetch.
  const uiSetup = backendCommand(
    "from apps.accounts.models import User; " +
    "from apps.games.models import Game; " +
    "from apps.matches.services import create_match_for_source, advance_match; " +
    "from django.utils import timezone; " +
    "a=User.objects.get(phone=" + JSON.stringify(seed.phones.alpha) + "); " +
    "b=User.objects.get(phone=" + JSON.stringify(seed.phones.bravo) + "); " +
    "g=Game.objects.get(slug=" + JSON.stringify(seed.gameSlug) + "); " +
    "m=create_match_for_source(source_kind='tournament', " +
    "source_id='b99-browser-dispute-ui-1', participant_a=a, participant_b=b, " +
    "game_id=g.pk, game_name=g.name, competition_title='B99 dispute UI acceptance', " +
    "tournament_slug='b99-dispute-ui', round_label='QA round', " +
    "starts_at=timezone.now()); " +
    "advance_match(m.pk, 'ready'); advance_match(m.pk, 'awaiting-result'); " +
    "print('B99_UI_DISPUTE_MATCH_ID='+str(m.pk))",
  );
  const uiMatchId = uiSetup.match(/B99_UI_DISPUTE_MATCH_ID=([0-9a-f-]{36})/)?.[1];
  assert(uiMatchId, "Disposable UI dispute match was not created");
  const uiResultEndpoint = "/api/v1/matches/" + uiMatchId + "/result/";
  const uiInitialResult = await readJson(a, uiResultEndpoint);
  assert.equal(uiInitialResult.status, 200);
  const uiSubmitted = await writeJson(a, uiResultEndpoint, {
    revision: uiInitialResult.payload.revision, playerScore: 4, opponentScore: 2,
  }, "b99-ui-dispute-score");
  assert.equal(uiSubmitted.status, 200);
  assert.equal(uiSubmitted.payload.outcome, "accepted");
  const uiResultB = await readJson(b, uiResultEndpoint);
  assert.equal(uiResultB.status, 200);
  const uiMismatch = await writeJson(b, uiResultEndpoint + "confirm/", {
    revision: uiResultB.payload.revision, playerScore: 3, opponentScore: 4,
  });
  assert.equal(uiMismatch.status, 200);
  assert.equal(uiMismatch.payload.outcome, "score_mismatch");

  const uiNavigation = await b.goto(base + "/matches/" + uiMatchId + "/dispute");
  try {
    await expect(b.getByRole("heading", { name: "اعتراض به Match" })).toBeVisible();
  } catch (error) {
    const apiDispute = await readJson(b, "/api/v1/matches/" + uiMatchId + "/dispute/");
    console.error("B99 dispute UI navigation diagnostics:", JSON.stringify({
      navigationStatus: uiNavigation?.status() ?? null,
      finalUrl: b.url(),
      pageTitle: await b.title(),
      visibleHeadings: await b.locator("h1,h2,[role=alert]").allInnerTexts().catch(() => []),
      apiStatus: apiDispute.status,
      apiDisputeState: apiDispute.payload?.disputeState ?? null,
      pageErrors,
    }));
    await b.screenshot({ path: artifacts + "/dispute-ui-navigation-failure.png", fullPage: true })
      .catch(() => null);
    throw error;
  }
  await expect(b.locator("#dispute-reason")).toBeVisible();
  await b.locator("#dispute-reason").selectOption("incorrect-score");
  await b.locator("#dispute-statement").fill(
    "The reported match score does not agree with the result seen by both players; please review the final score.",
  );
  await b.getByRole("button", { name: "بررسی اعتراض قبل از ثبت" }).click();
  await expect(b.getByRole("heading", { name: "قبل از ثبت یک بار بررسی کن" })).toBeVisible();
  const uiDisputePost = b.waitForResponse((response) =>
    new URL(response.url()).pathname === "/api/v1/matches/" + uiMatchId + "/dispute/" &&
    response.request().method() === "POST",
  );
  await b.getByRole("button", { name: "ثبت اعتراض", exact: true }).click();
  assert.equal((await uiDisputePost).status(), 200, "Dispute UI must POST to the real API");
  await expect(b.getByText("اعتراض ثبت شده است")).toBeVisible();
  for (const participant of [a, b]) {
    const uiDispute = await readJson(participant, "/api/v1/matches/" + uiMatchId + "/dispute/");
    assert.equal(uiDispute.status, 200);
    assert.equal(uiDispute.payload.disputeState, "open");
  }
  assert.equal((await readJson(third, "/api/v1/matches/" + uiMatchId + "/dispute/")).status, 404);
  // Exercise evidence upload through the actual React file input and multipart API.
  // The file is disposable, valid PNG, and must remain quarantined (no public URL).
  const evidenceBefore = await readJson(b, "/api/v1/matches/" + uiMatchId + "/dispute/");
  const uiDisputeId = evidenceBefore.payload?.dispute?.disputeId;
  assert.match(uiDisputeId, /^[0-9a-f-]{36}$/, "UI dispute must have a real UUID");
  assert.equal(evidenceBefore.payload.dispute.evidence.length, 0);
  const pngBytes = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lXcAAAAASUVORK5CYII=",
    "base64",
  );
  const evidenceEndpoint = "/api/v1/matches/" + uiMatchId + "/dispute/" + uiDisputeId + "/evidence/";
  await expect(b.getByRole("heading", { name: "مدارک پرونده" })).toBeVisible();
  await b.locator("#dispute-evidence").setInputFiles({
    name: "b99-evidence.png", mimeType: "image/png", buffer: pngBytes,
  });
  const evidencePost = b.waitForResponse((response) =>
    new URL(response.url()).pathname === evidenceEndpoint &&
    response.request().method() === "POST",
  );
  await b.getByRole("button", { name: "افزودن مدرک", exact: true }).click();
  const evidenceResponse = await evidencePost;
  assert.equal(evidenceResponse.status(), 200, "React evidence upload must reach the real API");
  const evidenceReceipt = await evidenceResponse.json();
  assert.equal(evidenceReceipt.outcome, "accepted");
  assert.equal(evidenceReceipt.matchId, uiMatchId);
  assert.equal(evidenceReceipt.disputeId, uiDisputeId);
  await expect(b.getByRole("list", { name: "مدارک ثبت‌شده" }).getByText("b99-evidence.png")).toBeVisible();
  const evidenceAfter = await readJson(b, "/api/v1/matches/" + uiMatchId + "/dispute/");
  assert.equal(evidenceAfter.status, 200);
  assert.equal(evidenceAfter.payload.dispute.evidence.length, 1);
  const evidenceMetadata = evidenceAfter.payload.dispute.evidence[0];
  assert.equal(evidenceMetadata.evidenceId, evidenceReceipt.evidence.evidenceId);
  assert.equal(evidenceMetadata.fileName, "b99-evidence.png");
  assert.equal(evidenceMetadata.sizeBytes, pngBytes.length);
  assert.deepEqual(Object.keys(evidenceMetadata).sort(),
    ["evidenceId", "fileName", "contentType", "sizeBytes", "uploadedAt"].sort(),
    "Evidence API must not expose quarantined bytes or storage URLs");

  // Participant cannot upload a spoofed PNG; outsider cannot upload to this dispute.
  async function attemptEvidence(page, revision, key, mime, bytes) {
    return page.evaluate(async (args) => {
      const csrfResponse = await fetch("/api/v1/auth/csrf/", { credentials: "include" });
      if (!csrfResponse.ok) throw new Error("CSRF bootstrap failed");
      const token = (await csrfResponse.json()).csrf_token;
      const form = new FormData();
      form.append("revision", args.revision);
      form.append("file", new Blob([new Uint8Array(args.bytes)], { type: args.mime }), "proof.png");
      const response = await fetch(args.endpoint, {
        method: "POST", credentials: "include",
        headers: { Accept: "application/json", "X-CSRFToken": token, "Idempotency-Key": args.key },
        body: form,
      });
      return { status: response.status, payload: await response.json().catch(() => null) };
    }, { endpoint: evidenceEndpoint, revision, key, mime, bytes: Array.from(bytes) });
  }
  const spoofed = await attemptEvidence(
    b, evidenceAfter.payload.revision, "b99-evidence-spoofed-png", "image/png",
    Buffer.from("not actually a PNG"),
  );
  assert.equal(spoofed.status, 200);
  assert.equal(spoofed.payload?.outcome, "validation_error", "Spoofed PNG must be rejected");
  const outsiderEvidence = await attemptEvidence(
    third, evidenceAfter.payload.revision, "b99-evidence-outsider", "image/png", pngBytes,
  );
  assert.equal(outsiderEvidence.status, 404, "Outsider must not upload evidence");
  const evidenceDb = backendCommand(
    "from apps.disputes.models import DisputeEvidence; " +
    "rows=DisputeEvidence.objects.filter(dispute_id=" + JSON.stringify(uiDisputeId) + "); " +
    "assert rows.count()==1; e=rows.get(); " +
    "assert str(e.uploaded_by_id)==" + JSON.stringify(bId) + "; " +
    "assert e.content_type=='image/png' and e.size_bytes==" + pngBytes.length + "; " +
    "assert bytes(e.quarantined_bytes)[:8]==bytes([137,80,78,71,13,10,26,10]); " +
    "print('B99_EVIDENCE_QUARANTINE_PASS')",
  );
  assert.match(evidenceDb, /B99_EVIDENCE_QUARANTINE_PASS/);
  console.log("B99 EVIDENCE UI PASS: React multipart, quarantined bytes, spoofed MIME and outsider denied");

  const uiDrain = backendCommand(
    "from django.core.management import call_command; " +
    "call_command('drain_b08_events', limit=100)",
  );
  assert.match(uiDrain, /Applied 0 B08 events/,
    "UI-opened dispute must not finalize or change rankings");
  console.log("B99 DISPUTE UI PASS: browser form review, real API POST, open state, outsider denied");

  await a.goto(base + "/matches/" + matchId + "/result");
  await expect(a.getByText("نتیجه Match نهایی شده است")).toBeVisible();
  await b.goto(base + "/dashboard/challenges");
  await expect(b.getByText("چالش‌های من")).toBeVisible();
  assert.deepEqual(pageErrors, [], "Frontend runtime errors: " + pageErrors.join(" / "));
  console.log("B99 REAL BROWSER PASS: independent OTP sessions, UI challenge, " +
    "single B08 match, CSRF/outsider denial, final result, once-only B09, dashboards");
} catch (error) {
  for (const [label, page] of [["A", a], ["B", b], ["third", third]]) {
    await page.screenshot({ path: artifacts + "/" + label + ".png", fullPage: true })
      .catch(() => {});
  }
  throw error;
} finally {
  await browser.close();
}
