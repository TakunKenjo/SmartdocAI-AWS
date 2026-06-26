import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircleIcon } from "lucide-react"

const FailedAlert = ({ title, description }) => {
    return (
        <Alert variant="destructive" className="max-w-md">
            <AlertCircleIcon />
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription>
                {description}
            </AlertDescription>
        </Alert>
    )
}
export default FailedAlert
