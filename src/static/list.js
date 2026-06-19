document.addEventListener("DOMContentLoaded", () => {
  fetch("static/contact_list.xlsx?v=" + Date.now())
    .then(res => res.arrayBuffer())
    .then(buffer => {
      const workbook = XLSX.read(buffer, { type: "array" });
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json(sheet);
      renderContacts(json);
    })
    .catch(err => {
      document.getElementById("contact-list").innerHTML =
        "<p class='text-red-500'>contact_list.xlsx の読み込みに失敗しました。</p>";
      console.error(err);
    });
});

function renderContacts(data) {
  const container = document.getElementById("contact-list");
  container.innerHTML = "";

  // Group by branch
  const grouped = {};
  data.forEach(row => {
    const branch = row["branch name"] || row["Branch Name"] || "未分類";
    if (!grouped[branch]) grouped[branch] = [];
    grouped[branch].push({
      name: row["name"] || row["Name"],
      phone: row["phone number"] || row["Phone Number"],
    });
  });

  // Render UI
  for (const branch in grouped) {
    const header = document.createElement("h2");
    header.id = "branch-header";
    header.className = "text-2xl font-bold mt-6 text-gray-800";
    header.textContent = branch;
    container.appendChild(header);

    grouped[branch].forEach(person => {
      const btn = document.createElement("div");
      btn.id = "contact-button";
    //   btn.className =
    //     "inline-block bg-green-500 hover:bg-green-600 text-white rounded-md px-4 py-2 mt-2 mr-2 cursor-pointer";
      btn.textContent = person.name;

      btn.onclick = () => {

        const base = window.location.origin + "/phone";
        const query =
          "#name=" + encodeURIComponent(person.name) +
          "&phone=" + encodeURIComponent(person.phone);
        window.location.href = base + query;
      };

      container.appendChild(btn);
    });
  }
}
