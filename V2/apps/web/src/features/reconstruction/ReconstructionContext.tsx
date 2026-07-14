import {
  createContext,
  useContext,
  useMemo,
  useReducer,
  type Dispatch,
  type PropsWithChildren,
} from "react";
import type { CompleteResponse, StockSummary, TradeConfig } from "../../shared/api/client";

type ReconstructionState = {
  selected: StockSummary[];
  trades: Record<string, TradeConfig>;
  result: CompleteResponse | null;
};

type Action =
  | { type: "toggle-stock"; stock: StockSummary }
  | { type: "set-trade"; trade: TradeConfig }
  | { type: "set-result"; result: CompleteResponse }
  | { type: "reset" };

type ReconstructionStore = ReconstructionState & { dispatch: Dispatch<Action> };

const initialState: ReconstructionState = { selected: [], trades: {}, result: null };
const ReconstructionContext = createContext<ReconstructionStore | null>(null);

function reducer(state: ReconstructionState, action: Action): ReconstructionState {
  switch (action.type) {
    case "toggle-stock": {
      const exists = state.selected.some((stock) => stock.id === action.stock.id);
      if (exists) {
        const trades = { ...state.trades };
        delete trades[action.stock.id];
        return {
          ...state,
          selected: state.selected.filter((stock) => stock.id !== action.stock.id),
          trades,
          result: null,
        };
      }
      if (state.selected.length >= 5) return state;
      return { ...state, selected: [...state.selected, action.stock], result: null };
    }
    case "set-trade":
      return {
        ...state,
        trades: { ...state.trades, [action.trade.stock_id]: action.trade },
        result: null,
      };
    case "set-result":
      return { ...state, result: action.result };
    case "reset":
      return initialState;
  }
}

export function ReconstructionProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const value = useMemo(() => ({ ...state, dispatch }), [state]);
  return <ReconstructionContext.Provider value={value}>{children}</ReconstructionContext.Provider>;
}

export function useReconstruction(): ReconstructionStore {
  const value = useContext(ReconstructionContext);
  if (!value) throw new Error("useReconstruction must be used inside ReconstructionProvider");
  return value;
}

export function defaultTrade(stock: StockSummary): TradeConfig {
  const buyMonth = stock.available_months[0] ?? "01";
  const availableAfterBuy = stock.available_months.filter((month) => Number(month) > Number(buyMonth));
  return {
    stock_id: stock.id,
    relation: "holding",
    buy_month: buyMonth,
    buy_mode: "band",
    buy_band: "mid",
    buy_exact: null,
    sell_month: availableAfterBuy.at(-1) ?? "12",
    sell_mode: "estimate",
    sell_exact: null,
  };
}
