const SUIT_ROW: Record<string, number> = {
  m: 0,
  s: 1,
  p: 2,
};

const HONOR_COL: Record<string, number> = {
  north: 0,
  white: 1,
  south: 2,
  red: 3,
  green: 4,
  east: 5,
  west: 6,
};

export function getTileSpritePosition(tile: string): string {
  const basic = /^([msp])(\d)$/.exec(tile);
  let row = 0;
  let col = 0;

  if (basic) {
    row = SUIT_ROW[basic[1]];
    col = Number.parseInt(basic[2], 10) - 1;
  } else {
    row = 3;
    col = HONOR_COL[tile] ?? 0;
  }

  const x = col * (100 / 8);
  const y = row * (100 / 3);
  return `${x}% ${y}%`;
}
