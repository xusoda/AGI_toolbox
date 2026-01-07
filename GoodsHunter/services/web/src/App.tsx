import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ItemsListPage from './pages/ItemsListPage'
import ItemDetailPage from './pages/ItemDetailPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ItemsListPage />} />
        <Route path="/items/:id" element={<ItemDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

