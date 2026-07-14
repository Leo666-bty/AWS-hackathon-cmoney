import { Link, useLocation, useNavigate } from "react-router-dom";
import { useReconstruction } from "../../features/reconstruction/ReconstructionContext";
import { clearMemberSession, hasMemberSession } from "../auth/session";

export function AppHeader() {
  const navigate = useNavigate();
  const location = useLocation();
  const { dispatch } = useReconstruction();

  const reset = () => {
    dispatch({ type: "reset" });
    void navigate("/");
  };

  return (
    <header className="topbar">
      <Link className="brand" to="/" onClick={() => dispatch({ type: "reset" })}>
        <i>M</i>
        <span><b>Mindfolio</b><small>TIME MACHINE V2</small></span>
      </Link>
      <div className="topbar-actions">
        <span className="db-status"><i />300 檔 2025 行情</span>
        {hasMemberSession() && location.pathname !== "/app" && <Link className="header-link" to="/app">Portfolio Radar</Link>}
        {location.pathname === "/app" ? <button className="text-button" type="button" onClick={() => { clearMemberSession(); reset(); }}>登出</button> : <button className="text-button" type="button" onClick={reset}>重新開始</button>}
      </div>
    </header>
  );
}
