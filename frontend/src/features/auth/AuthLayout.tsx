import styles from "./authLayout.module.css";
import { SectionTitle } from "@/src/components/atoms/title/SectionTitle";

export function AuthLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className={styles.page}>
            <div className={styles.background} aria-hidden />
            <SectionTitle title="Rebirth/リバース" className={styles.gameTitle} />
            <div className={styles.contentContainer}>{children}</div>
        </div>
    );
}
