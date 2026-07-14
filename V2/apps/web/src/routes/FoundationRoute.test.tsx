import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { FoundationRoute } from "./FoundationRoute";

describe("FoundationRoute", () => {
  it("shows the initialized architecture", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <QueryClientProvider client={client}>
        <FoundationRoute />
      </QueryClientProvider>,
    );

    expect(screen.getByText("React + TypeScript")).toBeInTheDocument();
    expect(screen.getByText("FastAPI + Python")).toBeInTheDocument();
    expect(screen.getByText("AI Training")).toBeInTheDocument();
  });
});
