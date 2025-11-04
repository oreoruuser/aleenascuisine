import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Loader } from "../components/Loader";

export const AuthCallbackPage = () => {
	const navigate = useNavigate();

	useEffect(() => {
		const url = new URL(window.location.href);
		const error = url.searchParams.get("error");
		const errorDescription = (url.searchParams.get("error_description") || "").toLowerCase();
		if (error && errorDescription.includes("not confirmed")) {
			const usernameParam = url.searchParams.get("username") || url.searchParams.get("userName");
			const verifyPath = usernameParam
				? `/verify?username=${encodeURIComponent(usernameParam)}`
				: "/verify";
			navigate(verifyPath, {
				replace: true,
				state: {
					error:
						"Your account is not verified yet. Enter the verification code sent to your email to finish signing up.",
					username: usernameParam ?? undefined,
				},
			});
			return;
		}
		const fromParam = url.searchParams.get("from");
		const nextPath = fromParam && fromParam.startsWith("/") ? fromParam : "/menu";
		const timer = window.setTimeout(() => {
			navigate(nextPath, { replace: true });
		}, 0);
		return () => window.clearTimeout(timer);
	}, [navigate]);

	return <Loader message="Completing sign in" />;
};
