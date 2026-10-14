/** Salomlashish: server display_name (Telegram) yoki first_name / username. */
export function greetingName(me) {
  if (!me) return "do‘st";
  const fromMe = me.display_name?.trim();
  if (fromMe) return fromMe;
  const first = me.user?.first_name?.trim();
  if (first) return first;
  const uname = me.user?.username;
  if (uname) return `@${uname}`;
  return "do‘st";
}
