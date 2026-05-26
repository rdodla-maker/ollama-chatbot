import Topbar from '../components/Topbar'
import ChatWindow from '../components/ChatWindow'
import PdfUpload from '../components/PdfUpload'
import { useChat } from '../hooks/useChat'

export default function RAGPage({ status }) {
  const { messages, loading, sendMessage, clearChat } = useChat({ stream: true })

  return (
    <div className="page page-rag">
      <Topbar
        title="PDF RAG"
        subtitle="Upload documents · semantic search · grounded answers"
        status={status}
        onClear={clearChat}
        clearLabel="Clear chat"
      />
      <div className="rag-layout">
        <div className="rag-upload-col">
          <PdfUpload />
        </div>
        <div className="rag-chat-col">
          <ChatWindow
            messages={messages}
            loading={loading}
            onSend={sendMessage}
            placeholder="Ask about your uploaded PDFs…"
            emptyTitle="Document chat"
            emptyDescription="Upload a PDF, then ask questions about its content."
          />
        </div>
      </div>
    </div>
  )
}
