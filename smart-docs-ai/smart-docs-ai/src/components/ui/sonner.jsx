import {useTheme} from "next-themes"
import {Toaster as Sonner} from "sonner";
import {CircleCheckIcon, InfoIcon, TriangleAlertIcon, OctagonXIcon, Loader2Icon} from "lucide-react"

const Toaster = ({
                     ...props
                 }) => {
    const {theme = "system"} = useTheme()

    return (
        <Sonner
            theme={theme}
            className="toaster group"
            icons={{
                success: (
                    <CircleCheckIcon className="size-5 text-emerald-600"/>
                ),
                info: (
                    <InfoIcon className="size-5 text-blue-500"/>
                ),
                warning: (
                    <TriangleAlertIcon className="size-5 text-yellow-500"/>
                ),
                error: (
                    <OctagonXIcon className="size-5 text-rose-600"/>
                ),
                loading: (
                    <Loader2Icon className="size-5 animate-spin"/>
                ),
            }}
            style={
                {
                    "--normal-bg": "var(--popover)",
                    "--normal-text": "var(--popover-foreground)",
                    "--normal-border": "var(--border)",
                    "--border-radius": "var(--radius)"
                }
            }
            toastOptions={{
                classNames: {
                    toast: "truncate",
                    description: "!text-slate-600 dark:!text-slate-300 text-sm",
                },
            }}
            {...props} />
    );
}

export {Toaster}
