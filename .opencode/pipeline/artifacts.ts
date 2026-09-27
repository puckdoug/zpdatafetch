export function findIssueArtifact(
  files: string[],
  issue: number,
  kind: "spec" | "design",
): string | null {
  const re = new RegExp(`^\\d{8}-gh${issue}-${kind}\\.md$`);
  for (const f of files) {
    if (re.test(f)) return f;
  }
  return null;
}

export function checklistComplete(markdown: string): boolean {
  const boxes = markdown.match(/^[ \t]*[-*][ \t]*\[[ xX]\]/gm) ?? [];
  if (boxes.length === 0) return false;
  return boxes.every((b) => /\[[xX]\]/.test(b));
}

export function hasOpenDeficiency(markdown: string): boolean {
  return /(^|\n)#{1,6}[ \t]+Open Deficiencies\b/.test(markdown);
}