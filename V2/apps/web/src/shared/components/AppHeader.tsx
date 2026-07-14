import { Link, useNavigate } from "react-router-dom";
import { useReconstruction } from "../../features/reconstruction/ReconstructionContext";

export function AppHeader() {
  const navigate = useNavigate();
  const { dispatch } = useReconstruction();

  const reset = () => {
    dispatch({ type: "reset" });
    navigate("/");
  };

  return (
    <header className="topbar">
      <Link className="brand" to="/" onClick={() => dispatch({ type: "reset" })}>
        <i>M</i>
        <span><b>Mindfolio</b><small>TIME MACHINE V2</small></span>
      </Link>
      <div className="topbar-actions">
        <span className="db-status"><i />300 檔 2025 行情</span>
        <button className="text-button" type="button" onClick={reset}>重新開始</button>
      </div>
    </header>
  );
}
