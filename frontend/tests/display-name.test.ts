import { describe, expect, test } from "bun:test";
import { resolveDisplayName, resolveInitials } from "../src/lib/display-name";

// Unit coverage for the shared name resolvers (issue #276): a user-typed
// nickname outranks every derived form everywhere a name is shown. DOM-free,
// matching this template's bun:test conventions (no jsdom).

const FULL = {
  nickname: "kodex",
  given_name: "Stub",
  family_name: "User",
  email: "stub@example.com",
};

describe("resolveDisplayName", () => {
  test("prefers the user-typed nickname over every derived form", () => {
    expect(resolveDisplayName(FULL)).toBe("kodex");
  });

  test("falls back to given + family when the nickname is absent", () => {
    expect(resolveDisplayName({ ...FULL, nickname: "" })).toBe("Stub User");
  });

  test("a whitespace-only nickname does not win", () => {
    expect(resolveDisplayName({ ...FULL, nickname: "   " })).toBe("Stub User");
  });

  test("trims when only one of given/family is present", () => {
    expect(resolveDisplayName({ ...FULL, nickname: "", family_name: "" })).toBe("Stub");
    expect(resolveDisplayName({ ...FULL, nickname: "", given_name: "" })).toBe("User");
  });

  test("falls back to the email local part, never the full address", () => {
    expect(resolveDisplayName({ ...FULL, nickname: "", given_name: "", family_name: "" })).toBe("stub");
  });

  test("zero-prop / null invocation resolves to an empty string, never throws (adr-22 rule 1)", () => {
    expect(resolveDisplayName(null)).toBe("");
    expect(resolveDisplayName(undefined)).toBe("");
    expect(resolveDisplayName({})).toBe("");
  });
});

describe("resolveInitials", () => {
  test("prefers the first two characters of the nickname, uppercased", () => {
    expect(resolveInitials(FULL)).toBe("KO");
  });

  test("a one-character nickname yields a one-character initial", () => {
    expect(resolveInitials({ ...FULL, nickname: "k" })).toBe("K");
  });

  test("falls back to given + family initials when the nickname is absent", () => {
    expect(resolveInitials({ ...FULL, nickname: "" })).toBe("SU");
  });

  test("falls back to the email initial when no name is present", () => {
    expect(resolveInitials({ ...FULL, nickname: "", given_name: "", family_name: "" })).toBe("S");
  });

  test("zero-prop / null invocation resolves to the safe placeholder, never throws (adr-22 rule 1)", () => {
    expect(resolveInitials(null)).toBe("?");
    expect(resolveInitials(undefined)).toBe("?");
    expect(resolveInitials({})).toBe("?");
  });
});
