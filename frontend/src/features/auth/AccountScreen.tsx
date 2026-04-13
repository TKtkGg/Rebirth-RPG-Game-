"use client"

import { useRouter } from "next/navigation";
import { ColorButton } from "@/src/components/atoms/button/ColorButton";
import { AuthLayout } from "./AuthLayout";
import styles from "./AccountScreen.module.css";

export default function AccountScreen() {
    const router = useRouter();
    return (
        <AuthLayout>
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
                <ColorButton variant="brown" className={styles.menuButton} onClick={() => {}}>
                    ゲストログイン
                </ColorButton>
            </div>
        </AuthLayout>
    );
}
