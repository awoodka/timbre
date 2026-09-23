// Gemini's emotional profiles mark key emotions with **bold**. Render those as <strong>
// instead of showing the asterisks; everything else stays plain text (no HTML parsing).
export default function ProfileText({ text }) {
  return text.split(/(\*\*[^*\s](?:[^*\n]*[^*\s])?\*\*)/g).map((part, i) =>
    part.length > 4 && part.startsWith('**') && part.endsWith('**')
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  )
}
