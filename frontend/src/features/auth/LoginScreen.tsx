"use client"

import { apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function LoginScreen() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    return(
        <div>
            <h1>ログイン</h1>
            <div>
                <label>ユーザー名</label>
                <input type="text" name="username" value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div>
                <label>パスワード</label>
                <input type="password" name="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <button onClick={() => {
                if (username === "" || password === "") {
                    alert("ユーザー名とパスワードを入力してください");
                    return;
                }
                apiPost('/api/auth/login/', {
                    username: username,
                    password: password,
                }).then((data: { ok: boolean }) => {
                    if (data.ok) {
                        router.push('/game/start/');
                    }
                }).catch((error: { message: string }) => {
                    alert(error.message);
                });
            }}>ログイン</button>
        </div>
    )
}