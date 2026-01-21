# Story E3-07 : Implémenter CRUD mémoire (voir, éditer, supprimer)

## Description

En tant que **utilisateur**,
Je veux **gérer ma mémoire (ajouter, modifier, supprimer)**,
Afin de **garder le contrôle sur mes données**.

## Contexte technique

- **Composants impactés** : Backend Python, Frontend React
- **Dépendances** : E3-01, E3-03, E3-06
- **Fichiers concernés** :
  - `src/backend/therese/api/routes/memory.py` (nouveau)
  - `src/frontend/src/components/memory/MemoryManager.tsx` (nouveau)
  - `src/frontend/src/components/memory/MemoryDetail.tsx` (nouveau)

## Critères d'acceptation

- [ ] Liste paginée de toutes les mémoires
- [ ] Filtres par type, catégorie, date
- [ ] Création manuelle d'une mémoire
- [ ] Édition d'une mémoire existante
- [ ] Suppression avec confirmation
- [ ] Export JSON/CSV de la mémoire
- [ ] Import depuis fichier JSON

## Notes techniques

### Routes API complètes

```python
# therese/api/routes/memory.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreate(BaseModel):
    type: str
    category: Optional[str] = None
    content: str
    tags: list[str] = []
    contact_id: Optional[str] = None
    project_id: Optional[str] = None


class MemoryUpdate(BaseModel):
    type: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None


@router.get("/")
async def list_memories(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Liste les mémoires avec pagination et filtres"""
    offset = (page - 1) * limit
    memories, total = memory_service.list(
        offset=offset,
        limit=limit,
        type_filter=type,
        category_filter=category,
        search=search
    )
    return {
        "items": memories,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/{memory_id}")
async def get_memory(memory_id: str):
    """Récupère une mémoire par son ID"""
    memory = memory_service.get(memory_id)
    if not memory:
        raise HTTPException(404, "Memory not found")
    return memory


@router.post("/")
async def create_memory(data: MemoryCreate):
    """Crée une nouvelle mémoire"""
    memory = memory_service.create(
        type=data.type,
        category=data.category,
        content=data.content,
        tags=data.tags,
        source="manual",
        contact_id=data.contact_id,
        project_id=data.project_id
    )
    # Indexer dans Qdrant
    await memory_index_service.index_memory(memory)
    return memory


@router.patch("/{memory_id}")
async def update_memory(memory_id: str, data: MemoryUpdate):
    """Met à jour une mémoire"""
    memory = memory_service.update(memory_id, **data.dict(exclude_unset=True))
    if not memory:
        raise HTTPException(404, "Memory not found")
    # Réindexer
    await memory_index_service.index_memory(memory)
    return memory


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Supprime une mémoire"""
    success = memory_service.delete(memory_id)
    if not success:
        raise HTTPException(404, "Memory not found")
    # Supprimer de l'index
    await memory_index_service.delete_memory(memory_id)
    return {"status": "deleted"}


@router.get("/export")
async def export_memories(format: str = Query("json", enum=["json", "csv"])):
    """Exporte toute la mémoire"""
    memories = memory_service.list_all()
    if format == "json":
        return {"memories": [m.dict() for m in memories]}
    else:
        # CSV format
        import io
        import csv
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "type", "category", "content", "tags", "created_at"])
        writer.writeheader()
        for m in memories:
            writer.writerow(m.dict())
        return output.getvalue()


@router.post("/import")
async def import_memories(data: list[MemoryCreate]):
    """Importe des mémoires depuis JSON"""
    imported = []
    for item in data:
        memory = await create_memory(item)
        imported.append(memory)
    return {"imported": len(imported)}
```

### Composant Memory Manager

```tsx
// components/memory/MemoryManager.tsx
import { useState } from 'react';
import { Plus, Search, Filter, Download, Upload } from 'lucide-react';

export function MemoryManager() {
  const [filters, setFilters] = useState({ type: '', category: '', search: '' });
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery(['memories', filters, page], () =>
    api.get('/memory', { params: { ...filters, page } })
  );

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-4 p-4 border-b border-border">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="w-full pl-10 pr-4 py-2 bg-surface-elevated rounded-lg text-text"
          />
        </div>

        <FilterDropdown
          value={filters.type}
          onChange={(type) => setFilters({ ...filters, type })}
          options={['fact', 'preference', 'note', 'skill']}
          placeholder="Type"
        />

        <button
          onClick={() => openCreateModal()}
          className="flex items-center gap-2 px-4 py-2 bg-accent-cyan text-bg rounded-lg"
        >
          <Plus size={16} />
          Ajouter
        </button>

        <ExportButton />
      </div>

      {/* Liste */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="text-center text-text-muted">Chargement...</div>
        ) : (
          <div className="space-y-2">
            {data?.items.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                onEdit={() => openEditModal(memory)}
                onDelete={() => confirmDelete(memory.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      <Pagination
        page={page}
        totalPages={data?.pages || 1}
        onPageChange={setPage}
      />
    </div>
  );
}

function MemoryCard({ memory, onEdit, onDelete }) {
  const typeColors = {
    fact: 'bg-blue-500/20 text-blue-400',
    preference: 'bg-purple-500/20 text-purple-400',
    note: 'bg-green-500/20 text-green-400',
    skill: 'bg-orange-500/20 text-orange-400',
  };

  return (
    <div className="p-4 bg-surface-elevated rounded-lg hover:bg-surface-elevated/80 group">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={cn('px-2 py-0.5 rounded text-xs', typeColors[memory.type])}>
              {memory.type}
            </span>
            {memory.category && (
              <span className="text-xs text-text-muted">{memory.category}</span>
            )}
          </div>
          <p className="text-text">{memory.content}</p>
          <div className="flex items-center gap-2 mt-2 text-xs text-text-muted">
            <span>{formatDate(memory.created_at)}</span>
            {memory.tags?.length > 0 && (
              <span>• {memory.tags.join(', ')}</span>
            )}
          </div>
        </div>

        <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1">
          <button onClick={onEdit} className="p-1 hover:bg-surface rounded">
            <Pencil size={14} />
          </button>
          <button onClick={onDelete} className="p-1 hover:bg-surface rounded text-error">
            <Trash size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Modal de création/édition

```tsx
// components/memory/MemoryModal.tsx
export function MemoryModal({ memory, onClose, onSave }) {
  const [formData, setFormData] = useState({
    type: memory?.type || 'note',
    category: memory?.category || '',
    content: memory?.content || '',
    tags: memory?.tags?.join(', ') || '',
  });

  const handleSubmit = async () => {
    await onSave({
      ...formData,
      tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
    });
    onClose();
  };

  return (
    <Modal title={memory ? 'Modifier la mémoire' : 'Ajouter une mémoire'} onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-text-muted mb-1">Type</label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            className="w-full px-3 py-2 bg-surface-elevated rounded-lg text-text"
          >
            <option value="fact">Fait</option>
            <option value="preference">Préférence</option>
            <option value="note">Note</option>
            <option value="skill">Compétence</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">Contenu</label>
          <textarea
            value={formData.content}
            onChange={(e) => setFormData({ ...formData, content: e.target.value })}
            rows={4}
            className="w-full px-3 py-2 bg-surface-elevated rounded-lg text-text resize-none"
          />
        </div>

        <div>
          <label className="block text-sm text-text-muted mb-1">Tags (séparés par des virgules)</label>
          <input
            type="text"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            placeholder="IA, tools, personnel"
            className="w-full px-3 py-2 bg-surface-elevated rounded-lg text-text"
          />
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <button onClick={onClose} className="px-4 py-2 text-text-muted hover:text-text">
            Annuler
          </button>
          <button onClick={handleSubmit} className="px-4 py-2 bg-accent-cyan text-bg rounded-lg">
            {memory ? 'Enregistrer' : 'Ajouter'}
          </button>
        </div>
      </div>
    </Modal>
  );
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] CRUD complet via API
- [ ] Interface liste + filtres
- [ ] Modal création/édition
- [ ] Suppression avec confirmation
- [ ] Export/Import fonctionnels
- [ ] Tests E2E

---

*Sprint : 3-4*
*Assigné : Agent Dev*
