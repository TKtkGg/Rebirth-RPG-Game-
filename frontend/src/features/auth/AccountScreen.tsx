"use client"

import { apiPost } from "@/src/lib/apiClient";
import { useRouter } from "next/navigation";
import { ColorButton } from "@/src/components/atoms/button/ColorButton";
import { AuthLayout } from "./AuthLayout";
import styles from "./AccountScreen.module.css";
import { useState } from "react";

export default function AccountScreen() {
    const router = useRouter();
    const [errorMessage, setErrorMessage] = useState("");
    return (
        <AuthLayout>
            {errorMessage ? (
                <div className={styles.errorMessage}>
                    {errorMessage}
                </div>
            ) : null}
            <div className={styles.buttonStack}>
                <ColorButton
                    variant="brown"
                    className={styles.menuButton}
                    onClick={() => router.push("/auth/signup")}
                >
                    アカウント登録
                </ColorButton>
                <ColorButton
                    variant="brown"
                    className={styles.menuButton}
                    onClick={() => router.push("/auth/login")}
                >
                    ログイン
                </ColorButton>
                <ColorButton variant="brown" className={styles.menuButton} onClick={() => {
                    apiPost("/api/auth/guest-login/", { username: "guest" }).then((data: { ok: boolean }) => {
                        if (data.ok) {
                            router.push("/game/start/");
                        }else{
                            setErrorMessage("ゲストログインに失敗しました。");
                        }
                    }).catch(() => {
                        setErrorMessage("ゲストログインに失敗しました。");
                    });
                }}>
                    ゲストログイン
                </ColorButton>
            </div>
        </AuthLayout>
    );
}
