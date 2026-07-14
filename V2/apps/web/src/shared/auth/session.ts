const ACCESS_TOKEN_KEY = "mindfolio_v2_access_token";
const MEMBER_ID_KEY = "mindfolio_v2_member_id";

export function getAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function saveMemberSession(accessToken: string, memberId: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(MEMBER_ID_KEY, memberId);
}

export function clearMemberSession(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(MEMBER_ID_KEY);
}

export function hasMemberSession(): boolean {
  return Boolean(getAccessToken());
}
