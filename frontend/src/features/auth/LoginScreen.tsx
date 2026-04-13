"use client"

import { apiPost, apiGet } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ColorButton } from "@/src/components/atoms/button/ColorButton";
import { AuthLayout } from "./AuthLayout";
import layoutStyles from "./authLayout.module.css";

type session = {
    is_authenticated: boolean;
    user: {
        id: number;
        username: string;
    } | null;
    player_id: string | null;
};

export default function LoginScreen() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    return (
        <AuthLayout>
            <div className={layoutStyles.authContainer}>
                <div className={layoutStyles.authBox}>
                    <h2 className={layoutStyles.authHeading}>ログイン</h2>

                    {errorMessage ? (
                        <div className={layoutStyles.errorMessages}>
                            <p>{errorMessage}</p>
                        </div>
                    ) : null}

                    <div className={layoutStyles.formGroup}>
                        <label htmlFor="login-username" className={layoutStyles.label}>
                            ユーザー名
                        </label>
                        <input
                            id="login-username"
                            className={layoutStyles.input}
                            type="text"
                            name="username"
                            autoComplete="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>
                    <div className={layoutStyles.formGroup}>
                        <label htmlFor="login-password" className={layoutStyles.label}>
                            パスワード
                        </label>
                        <input
                            id="login-password"
                            className={layoutStyles.input}
                            type="password"
                            name="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    <div className={layoutStyles.submitWrap}>
                        <ColorButton
                            variant="brown"
                            className={layoutStyles.submitButton}
                            onClick={() => {
                                if (username === "" || password === "") {
                                    setErrorMessage("ユーザー名とパスワードを入力してください");
                                    return;
                                }
                                setErrorMessage("");
                                apiPost("/api/auth/login/", {
                                    username: username,
                                    password: password,
                                })
                                    .then((data: { ok: boolean }) => {
                                        if (data.ok) {
                                            apiGet("/api/auth/session/").then((data: session) => {
                                                if (data.player_id) {
                                                    const playerId = data.player_id;
                                                    router.push(`/game/battle/home/${playerId}/`);
                                                } else {
                                                    router.push("/game/start/");
                                                }
                                            });
                                        }
                                    })
                                    .catch(() => {
                                        setErrorMessage("ユーザーネームまたはパスワードが正しくありません。");
                                    });
                            }}
                        >
                            ログイン
                        </ColorButton>
                    </div>

                    <div className={layoutStyles.backLink}>
                        <button type="button" onClick={() => router.push("/auth/")}>
                            ← ホームに戻る
                        </button>
                    </div>
                </div>
            </div>
        </AuthLayout>
    );
}
