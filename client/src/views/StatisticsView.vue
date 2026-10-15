<template>
  <div class="statistics-page">
    <iframe src="/statistics/" title="Статистика фитнес-клуба" class="statistics-frame"></iframe>
  </div>
</template>

<style scoped>
.statistics-page {
  width: 100%;
}

.statistics-frame {
  display: block;
  width: 100%;
  height: calc(100vh - 110px);
  min-height: 650px;
  border: none;
}
</style>