"use client"

import { apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ColorButton } from "@/src/components/atoms/button/ColorButton";
import { AuthLayout } from "./AuthLayout";
import layoutStyles from "./authLayout.module.css";

export default function SignUpScreen() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password1, setPassword1] = useState("");
    const [password2, setPassword2] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    return (
        <AuthLayout>
            <div className={layoutStyles.authContainer}>
                <div className={layoutStyles.authBox}>
                    <h2 className={layoutStyles.authHeading}>新規アカウント作成</h2>

                    {errorMessage ? (
                        <div className={layoutStyles.errorMessages}>
                            <p>{errorMessage}</p>
                        </div>
                    ) : null}

                    <div className={layoutStyles.formGroup}>
                        <label htmlFor="signup-username" className={layoutStyles.label}>
                            ユーザー名
                        </label>
                        <input
                            id="signup-username"
                            className={layoutStyles.input}
                            type="text"
                            name="username"
                            autoComplete="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>
                    <div className={layoutStyles.formGroup}>
                        <label htmlFor="signup-password1" className={layoutStyles.label}>
                            パスワード
                        </label>
                        <input
                            id="signup-password1"
                            className={layoutStyles.input}
                            type="password"
                            name="password1"
                            autoComplete="new-password"
                            value={password1}
                            onChange={(e) => setPassword1(e.target.value)}
                        />
                    </div>
                    <div className={layoutStyles.formGroup}>
                        <label htmlFor="signup-password2" className={layoutStyles.label}>
                            パスワード（確認）
                        </label>
                        <input
                            id="signup-password2"
                            className={layoutStyles.input}
                            type="password"
                            name="password2"
                            autoComplete="new-password"
                            value={password2}
                            onChange={(e) => setPassword2(e.target.value)}
                        />
                    </div>

                    <div className={layoutStyles.submitWrap}>
                        <ColorButton
                            variant="brown"
                            className={layoutStyles.submitButton}
                            onClick={() => {
                                if (username === "" || password1 === "" || password2 === "") {
                                    setErrorMessage("ユーザー名とパスワードを入力してください");
                                    return;
                                }
                                if (password1 !== password2) {
                                    setErrorMessage("パスワードとパスワード（確認）が一致しません");
                                    return;
                                }
                                setErrorMessage("");
                                apiPost("/api/auth/signup/", {
                                    username: username,
                                    password1: password1,
                                    password2: password2,
                                })
                                    .then((data: { ok: boolean }) => {
                                        if (data.ok) {
                                            router.push("/game/start/");
                                        }
                                    })
                                    .catch((error: { message: string }) => {
                                        setErrorMessage(error.message);
                                    });
                            }}
                        >
                            アカウント作成
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
