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

  // Operator advances real B08 match lifecycle; players own score/confirmation.
  backendCommand(
    "from apps.matches.services import advance_match; " +
    "advance_match('" + matchId + "', 'ready'); " +
    "advance_match('" + matchId + "', 'awaiting-result')",
  );
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
