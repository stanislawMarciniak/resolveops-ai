import { Component, type ErrorInfo, type ReactNode } from "react";
import { ErrorPanel } from "@/components/ui/ErrorPanel";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("UI error boundary", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <ErrorPanel
          title="UI crashed"
          message={this.state.error.message}
          onRetry={() => this.setState({ error: null })}
        />
      );
    }

    return this.props.children;
  }
}
