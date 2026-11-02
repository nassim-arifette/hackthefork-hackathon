# Logo et mascotte

| Fichier | Usage |
|---|---|
| `logo.png` (1024 px), `logo-512.png`, `logo-256.png` | logo seul, fond transparent |
| `logo-horizontal.png`, `logo-horizontal-sombre.png` | logo et nom, sur fond clair ou sombre |
| `avatar.png` | avatar d'organisation ou de dépôt (fond plein, recadré en cercle par GitHub) |
| `social-preview.png` (1280 × 640) | aperçu social du dépôt : *Settings → General → Social preview* |
| `mascotte.png` (1024 px), `mascotte-512.png` | mascotte, fond transparent : README, deck, ouverture du pitch |
| `../../app/src/assets/` | favicon 32 px, icône Apple 180 px, logo 64 px du bandeau |
| `../../app/public/favicon.ico` | favicon 16, 32 et 48 px |

Couleurs et polices : celles de l'application ([DESIGN.md](../DESIGN.md)).

## Provenance

Images générées par OpenAI `gpt-image-2.5-sunburst` (1024 × 1024, fond transparent), puis recadrées et déclinées en Python (Pillow) : ombre portée du logo retirée par un masque arrondi, nom composé en Archivo.

- **Logo** : « App icon: a rounded-square tile in soft cream, inside it a big glossy 3D green lentil seed (flat round lens shape, mottled green) with a cute minimal face (two eyes, small smile) wearing a tiny straw hat, sitting securely on a thick golden bar like a shelf, a wheat ear leaning behind it. Clay-like 3D, front view, centered, bold simple shapes. »
- **Mascotte** : « Brand mascot for a French farming cooperative startup: a charming 3D character that is a single green lentil seed (a flat, round, biconvex lens-shaped seed, mottled olive green like a French Puy lentil, clearly a lentil not a ball or a pea), with big friendly confident eyes, a woven straw farmer hat, tiny arms and small brown boots. It stands firmly with one hand on its hip and proudly holds up a rolled paper contract tied with a green ribbon and a red wax seal. Pixar/Illumination quality, full body, centered. »

Les deux prompts se terminent par la même consigne de style : « Palette: lentil green #2F6A50 to fresh #6FA85A, wheat gold #C8962F, warm cream, dark ink #1D211C. Premium 3D render, soft studio lighting, subtle soft shadow under the subject, clean silhouette that reads at small size. Absolutely no text, no letters, no numbers anywhere in the image. »
