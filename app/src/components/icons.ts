// Icônes de la carte (camions, silo, bateau), dessinées dans un canvas puis passées à deck.gl en PNG.
// Pas de fichier image : tout tient dans le fichier HTML unique de la démo.

const CELL = 64;
const INK = '#1d211c', INK2 = '#454b43', LENTIL = '#2f6a50', SLATE = '#5b7385', WHEAT = '#c8962f';

type Ctx = CanvasRenderingContext2D;

function halo(g: Ctx, draw: () => void) {
  // Contour blanc sous chaque forme : l'icône reste lisible sur les parcelles ocre et vertes.
  g.save(); g.strokeStyle = '#fff'; g.lineWidth = 5; g.lineJoin = 'round'; draw(); g.stroke(); g.restore();
  draw(); g.fill();
}

function rect(g: Ctx, x: number, y: number, w: number, h: number, r = 2) {
  g.beginPath(); g.roundRect(x, y, w, h, r);
}

function truck(g: Ctx) {
  // Camion tourné vers la droite, benne verte (des lentilles), cabine noire.
  g.fillStyle = LENTIL; halo(g, () => rect(g, 6, 20, 34, 22, 3));
  g.fillStyle = INK; halo(g, () => { g.beginPath(); g.moveTo(41, 26); g.lineTo(51, 26); g.lineTo(58, 34); g.lineTo(58, 42); g.lineTo(41, 42); g.closePath(); });
  g.fillStyle = '#dfe7e2'; rect(g, 44, 29, 7, 6, 1); g.fill();
  for (const x of [16, 31, 50]) {
    g.fillStyle = INK; halo(g, () => { g.beginPath(); g.arc(x, 45, 5, 0, Math.PI * 2); });
    g.fillStyle = '#fff'; g.beginPath(); g.arc(x, 45, 1.8, 0, Math.PI * 2); g.fill();
  }
}

function silo(g: Ctx) {
  // Deux cellules de silo et un bâtiment bas : le site de collecte de la coopérative.
  g.fillStyle = INK2;
  halo(g, () => { g.beginPath(); g.moveTo(14, 56); g.lineTo(14, 18); g.arc(22, 18, 8, Math.PI, 0); g.lineTo(30, 56); g.closePath(); });
  halo(g, () => { g.beginPath(); g.moveTo(31, 56); g.lineTo(31, 22); g.arc(39, 22, 8, Math.PI, 0); g.lineTo(47, 56); g.closePath(); });
  g.fillStyle = INK; halo(g, () => rect(g, 46, 38, 14, 18, 1));
  g.strokeStyle = 'rgba(255,255,255,.55)'; g.lineWidth = 1.2;
  for (const y of [28, 38, 48]) { g.beginPath(); g.moveTo(15, y); g.lineTo(29, y); g.moveTo(32, y + 2); g.lineTo(46, y + 2); g.stroke(); }
}

function boat(g: Ctx) {
  // Cargo vu de profil : coque sombre, conteneurs sur le pont.
  g.fillStyle = INK; halo(g, () => { g.beginPath(); g.moveTo(4, 36); g.lineTo(60, 36); g.lineTo(52, 50); g.lineTo(11, 50); g.closePath(); });
  g.fillStyle = SLATE; halo(g, () => rect(g, 14, 24, 12, 11, 1));
  g.fillStyle = WHEAT; halo(g, () => rect(g, 27, 24, 12, 11, 1));
  g.fillStyle = SLATE; halo(g, () => rect(g, 40, 24, 10, 11, 1));
  g.fillStyle = INK2; halo(g, () => rect(g, 47, 14, 7, 21, 1));
}

function draw(fn: (g: Ctx) => void, g: Ctx, col: number, flip = false) {
  g.save();
  g.translate(col * CELL + (flip ? CELL : 0), 0);
  if (flip) g.scale(-1, 1);
  fn(g);
  g.restore();
}

function atlasUrl(): string {
  if (typeof document === 'undefined') return '';
  const c = document.createElement('canvas');
  c.width = CELL * 4; c.height = CELL;
  const g = c.getContext('2d');
  if (!g || !('roundRect' in g)) return '';
  draw(truck, g, 0);
  draw(truck, g, 1, true);
  draw(silo, g, 2);
  draw(boat, g, 3);
  return c.toDataURL('image/png');
}

export const ICON_ATLAS = atlasUrl();
const cell = (i: number) => ({ x: i * CELL, y: 0, width: CELL, height: CELL, anchorY: CELL / 2, mask: false });
export const ICON_MAPPING = { truckR: cell(0), truckL: cell(1), silo: { ...cell(2), anchorY: CELL - 6 }, boat: cell(3) };
export type IconName = keyof typeof ICON_MAPPING;
