import "@fortawesome/fontawesome-free";
import Sortable from 'sortablejs';
import NotifyX from "notifyx";
import "notifyx/style.css"

const modules = document.getElementById("modules");
const contents = document.getElementById("module-contents");

Sortable.create(modules!, {
    onUpdate: () => {
        const updateModuleOrderUrl = contents!.dataset.updateContentOrderUrl!;
        const modulesListArr = Array.from(modules?.children!)
        const moduleList = modulesListArr.reduce((acc, arr, index) => {
            // @ts-ignore
            acc[arr.dataset.id] = index + 1;
            return acc;
        }, {})

        const options = {
            method: "POST",
            mode: "same-origin",
            body: JSON.stringify(moduleList)
        } as RequestInit

        fetch(updateModuleOrderUrl, options).then(() => NotifyX.success("Urutan modul berhasil diperbarui")).catch(() => NotifyX.error("Gagal memperbarui urutan modul"));
    }
})
Sortable.create(contents!, {
    onUpdate: () => {
        const updateContentOrderUrl = contents!.dataset.updateContentOrderUrl!;
        const contentsListArr = Array.from(contents?.children!)
        const contentList = contentsListArr.reduce((acc, arr, index) => {
            // @ts-ignore
            acc[arr.dataset.id] = index + 1;
            return acc;
        }, {})

        const options = {
            method: "POST",
            mode: "same-origin",
            body: JSON.stringify(contentList)
        } as RequestInit

        fetch(updateContentOrderUrl, options).then(() => NotifyX.success("Urutan konten berhasil diperbarui")).catch(() => NotifyX.error("Gagal memperbarui urutan konten"));
    }
})

document.body.addEventListener("contentDeleted", () => {
    NotifyX.success("Konten berhasil dihapus");
})