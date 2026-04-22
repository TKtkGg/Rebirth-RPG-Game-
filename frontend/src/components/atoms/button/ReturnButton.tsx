import type { ReactNode } from "react";
import styles from "./button.module.css";

type Props = {
    onClick: () => void;
    children?: ReactNode;
    className?: string;
};

export const ReturnButton = ({ onClick, children = "戻る", className }: Props) => {
    return (
        <button
            type="button"
            className={`${styles.primaryButton} ${className ?? ""}`}
            onClick={onClick}
        >
            {children}
        </button>
    );
};
