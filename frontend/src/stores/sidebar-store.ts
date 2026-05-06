import { create } from 'zustand';

interface SidebarStore {
  isOpen: boolean;
  isCollapsed: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
  collapse: () => void;
  expand: () => void;
  toggleCollapse: () => void;
}

export const useSidebarStore = create<SidebarStore>((set) => ({
  isOpen: true,
  isCollapsed: false,

  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
  collapse: () => set({ isCollapsed: true }),
  expand: () => set({ isCollapsed: false }),
  toggleCollapse: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
}));
