import styles from "./authLayout.module.css";

export function AuthLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className={styles.page}>
            <div className={styles.background} aria-hidden />
            <h1 className={styles.gameTitle}>Rebirth/リバース</h1>
            <div className={styles.contentContainer}>{children}</div>
        </div>
    );
}
