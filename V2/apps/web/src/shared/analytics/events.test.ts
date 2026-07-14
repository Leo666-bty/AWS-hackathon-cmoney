import { afterEach, describe, expect, it, vi } from "vitest";
import { createClientId } from "./events";

const originalCrypto = globalThis.crypto;

afterEach(() => {
  vi.stubGlobal("crypto", originalCrypto);
});

describe("createClientId", () => {
  it("uses randomUUID when the browser provides it", () => {
    const randomUUID = vi.fn(() => "12345678-1234-4234-8234-123456789abc");
    vi.stubGlobal("crypto", { randomUUID });

    expect(createClientId()).toBe("12345678-1234-4234-8234-123456789abc");
    expect(randomUUID).toHaveBeenCalledOnce();
  });

  it("falls back to getRandomValues when randomUUID is unavailable on HTTP", () => {
    vi.stubGlobal("crypto", {
      getRandomValues: (bytes: Uint8Array) => {
        bytes.forEach((_, index) => { bytes[index] = index; });
        return bytes;
      },
    });

    expect(createClientId()).toBe("00010203-0405-4607-8809-0a0b0c0d0e0f");
  });
});
