const explicit_loopback_port = /^http:\/\/127\.0\.0\.1:\d{1,5}(?:[/?#]|$)/;

export function validate_jupyter_url(value) {
  if (typeof value !== "string" || !explicit_loopback_port.test(value)) {
    return null;
  }
  try {
    const url = new URL(value);
    if (
      url.protocol !== "http:" ||
      url.hostname !== "127.0.0.1" ||
      url.username ||
      url.password
    ) {
      return null;
    }
    return value;
  } catch {
    return null;
  }
}
