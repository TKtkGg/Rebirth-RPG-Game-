import styles from './panel.module.css'

export const InventoryPanel = ({ children, state, interactive, as, className, onClick, disabled }: { children: React.ReactNode, state: "normal" | "selected" | "muted", interactive: boolean, as?: "div" | "button", className?: string, onClick?: () => void, disabled?: boolean }) => {
    const Tag = as || "div";
    const isButton = as === "button";
    return(
        <Tag className={[
            styles.panel, 
            styles.beige,
            styles[state], 
            interactive ? styles.interactive : "",
            className ?? ""
            ].join(" ").trim()}
            onClick={isButton ? onClick : undefined}
            disabled={isButton ? disabled : undefined}
        >
            {children}
        </Tag>
    )
}