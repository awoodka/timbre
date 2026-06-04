// Visual identity per medium. Keep these colors as the single source of truth so
// the catalogue filter pills and the card borders always match.
export const MEDIA_TYPES = {
  book: { label: 'Book', color: '#b48b6e' }, // warm terracotta (matches --accent)
  film: { label: 'Film', color: '#6e8db4' }, // cool blue (complement)
  show: { label: 'Show', color: '#6e9e78' }, // sage green
  anime: { label: 'Anime', color: '#a06eb4' }, // plum
  manga: { label: 'Manga', color: '#6e8a8a' }, // slate-teal
  game: { label: 'Game', color: '#b8663a' }, // rust orange
}

export function getMediaType(medium) {
  return MEDIA_TYPES[medium] || { label: medium || 'Media', color: '#8a7f76' }
}
