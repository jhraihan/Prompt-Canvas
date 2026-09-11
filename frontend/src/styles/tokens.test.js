import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const CSS = readFileSync(resolve(process.cwd(), "src/styles/tokens.css"), "utf8");

function blockAt(startIndex) {
  const open = CSS.indexOf("{", startIndex);
  let depth = 0;
  for (let i = open; i < CSS.length; i += 1) {
    if (CSS[i] === "{") depth += 1;
    else if (CSS[i] === "}") {
      depth -= 1;
      if (depth === 0) return CSS.slice(open + 1, i);
    }
  }
  throw new Error("Unbalanced braces in tokens.css");
}

function tokensIn(text) {
  return new Set(
    [...text.matchAll(/^\s*(--pc-[a-z0-9-]+)\s*:/gm)].map((m) => m[1]),
  );
}

const baseTokens = tokensIn(blockAt(CSS.indexOf(":root {")));
const explicitDark = tokensIn(blockAt(CSS.indexOf(':root[data-theme="dark"]')));
const mediaDark = tokensIn(
  blockAt(CSS.indexOf(":root", CSS.indexOf("prefers-color-scheme: dark"))),
);

describe("dark theme definitions", () => {
  it("defines tokens in both places", () => {
    expect(explicitDark.size).toBeGreaterThan(20);
    expect(mediaDark.size).toBeGreaterThan(20);
  });

  it("declares an identical token set in both blocks", () => {
    const onlyExplicit = [...explicitDark].filter((t) => !mediaDark.has(t));
    const onlyMedia = [...mediaDark].filter((t) => !explicitDark.has(t));

    expect({ onlyExplicit, onlyMedia }).toEqual({
      onlyExplicit: [],
      onlyMedia: [],
    });
  });

  it("overrides only tokens the base theme actually defines", () => {
    const undefinedInBase = [...explicitDark].filter((t) => !baseTokens.has(t));
    expect(undefinedInBase).toEqual([]);
  });
});

describe("theme selectors", () => {
  it('has no rule matching data-theme="system"', () => {

    expect(CSS).not.toMatch(/\[data-theme=["']system["']\]/);
  });

  it("has no selector depending on a class nothing applies", () => {
    expect(CSS).not.toContain("light-preferred");
  });
});
