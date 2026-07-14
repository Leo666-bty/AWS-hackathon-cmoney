import "@testing-library/jest-dom/vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { LandingRoute } from "./LandingRoute";

describe("LandingRoute", () => {
  it("presents the zero-upload reconstruction entry", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter><LandingRoute /></MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /重建五檔記憶/ })).toBeInTheDocument();
    expect(screen.getByText(/不連券商、不上傳截圖/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /匿名開始重建/ })).toHaveAttribute("href", "/builder");
  });
});
