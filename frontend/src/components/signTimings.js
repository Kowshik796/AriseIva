/**
 * signTimings.js — Core signing window config for each ISL sign video.
 *
 * PURPOSE:
 *   Each .mp4 typically starts and ends with a neutral hand pose.
 *   This file lets you trim to the exact frame range where the actual
 *   sign movement occurs, so sequential playback looks like continuous
 *   natural signing rather than isolated clips with pauses between them.
 *
 * FORMAT:
 *   "GLOSS_TOKEN": { start: <seconds>, end: <seconds> }
 *
 * HOW TO MEASURE TIMINGS:
 *   1. Open the .mp4 in VLC or any video player
 *   2. Find the frame where hand movement STARTS → note the time in seconds
 *   3. Find the frame where hand returns to neutral → note the time
 *   4. Enter those values as start and end below
 *
 * DEFAULT BEHAVIOUR:
 *   Tokens without an entry here play their FULL video automatically.
 *   All entries are commented out by default — uncomment and fill in
 *   values as you measure each video manually.
 *
 * EXAMPLE:
 *   If HELLO.mp4 is 2.4s long but the actual sign runs from 0.3s to 1.9s:
 *   "HELLO": { start: 0.3, end: 1.9 }
 */

const signTimings = {

  // ── Pronouns ───────────────────────────────────────────────────────────────
  // "ME":        { start: 0.0, end: 1.0 },
  // "YOU":       { start: 0.0, end: 1.0 },
  // "HE":        { start: 0.0, end: 1.0 },
  // "SHE":       { start: 0.0, end: 1.0 },
  // "WE":        { start: 0.0, end: 1.0 },
  // "THEY":      { start: 0.0, end: 1.0 },

  // ── Common verbs ───────────────────────────────────────────────────────────
  // "GO":        { start: 0.0, end: 1.2 },
  // "COME":      { start: 0.0, end: 1.2 },
  // "EAT":       { start: 0.0, end: 1.5 },
  // "DRINK":     { start: 0.0, end: 1.5 },
  // "SLEEP":     { start: 0.0, end: 1.8 },
  // "WALK":      { start: 0.0, end: 1.4 },
  // "RUN":       { start: 0.0, end: 1.0 },
  // "STUDY":     { start: 0.0, end: 1.6 },
  // "WORK":      { start: 0.0, end: 1.4 },
  // "HELP":      { start: 0.0, end: 1.3 },
  // "WANT":      { start: 0.0, end: 1.2 },
  // "LIKE":      { start: 0.0, end: 1.3 },
  // "KNOW":      { start: 0.0, end: 1.2 },
  // "THINK":     { start: 0.0, end: 1.4 },
  // "SEE":       { start: 0.0, end: 1.0 },
  // "SPEAK":     { start: 0.0, end: 1.5 },
  // "UNDERSTAND":{ start: 0.0, end: 2.0 },

  // ── Places ─────────────────────────────────────────────────────────────────
  // "SCHOOL":    { start: 0.0, end: 1.8 },
  // "HOME":      { start: 0.0, end: 1.2 },
  // "HOSPITAL":  { start: 0.0, end: 2.0 },
  // "MARKET":    { start: 0.0, end: 1.6 },

  // ── Time words ─────────────────────────────────────────────────────────────
  // "TODAY":     { start: 0.0, end: 1.5 },
  // "TOMORROW":  { start: 0.0, end: 1.8 },
  // "YESTERDAY": { start: 0.0, end: 2.0 },
  // "NOW":       { start: 0.0, end: 0.9 },
  // "MORNING":   { start: 0.0, end: 1.6 },
  // "NIGHT":     { start: 0.0, end: 1.4 },

  // ── Questions ──────────────────────────────────────────────────────────────
  // "WHERE":     { start: 0.0, end: 1.4 },
  // "WHAT":      { start: 0.0, end: 1.2 },
  // "WHEN":      { start: 0.0, end: 1.3 },
  // "WHO":       { start: 0.0, end: 1.0 },
  // "WHY":       { start: 0.0, end: 1.2 },
  // "HOW":       { start: 0.0, end: 1.1 },

  // ── Negation ───────────────────────────────────────────────────────────────
  // "NO":        { start: 0.0, end: 1.0 },
  // "NEVER":     { start: 0.0, end: 1.5 },

  // ── Social ─────────────────────────────────────────────────────────────────
  // "HELLO":     { start: 0.0, end: 1.2 },
  // "THANK-YOU": { start: 0.0, end: 1.8 },
  // "SORRY":     { start: 0.0, end: 1.6 },
  // "PLEASE":    { start: 0.0, end: 1.4 },
  // "YES":       { start: 0.0, end: 0.8 },

};

export default signTimings;