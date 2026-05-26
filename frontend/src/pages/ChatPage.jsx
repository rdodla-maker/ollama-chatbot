import Topbar from '../components/Topbar'
import ChatWindow from '../components/ChatWindow'
import { useChat } from '../hooks/useChat'

export default function ChatPage({ status }) {
  const { messages, loading, sendMessage, clearChat } = useChat({ stream: true })

  return (
    <div className="page">
      <Topbar
        title="Chat"
        subtitle="Quick conversation with your local LLM via RAG"
        status={status}
        onClear={clearChat}
        clearLabel="Clear chat"
      />
      <ChatWindow
        messages={messages}
        loading={loading}
        onSend={sendMessage}
        placeholder="Ask anything…"
        emptyTitle="Your AI workspace"
        emptyDescription="Start chatting. Connect PDF RAG for document-aware answers."
      />
    </div>
  )
}
