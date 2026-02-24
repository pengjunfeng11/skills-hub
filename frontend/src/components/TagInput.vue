<template>
  <div>
    <div class="flex flex-wrap items-center gap-1.5 p-2 border border-gray-300 rounded-xl focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all bg-white min-h-[42px]">
      <span
        v-for="tag in tags"
        :key="tag"
        class="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-light text-primary text-xs font-medium rounded-lg"
      >
        {{ tag }}
        <button type="button" @click.stop="removeTag(tag)" class="hover:text-primary-dark cursor-pointer ml-0.5 bg-transparent border-none p-0 leading-none">
          <span class="material-icons-round text-[14px]">close</span>
        </button>
      </span>
      <input
        v-model="input"
        :placeholder="tags.length ? '' : placeholder"
        class="flex-1 min-w-[120px] border-none outline-none text-sm bg-transparent py-1 px-1"
        @keydown.enter.prevent="addTag"
        @keydown.backspace="handleBackspace"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: '输入后回车添加' },
})

const emit = defineEmits(['update:modelValue'])
const input = ref('')

const tags = computed(() => props.modelValue || [])

function addTag() {
  const val = input.value.trim()
  if (val && !tags.value.includes(val)) {
    emit('update:modelValue', [...tags.value, val])
  }
  input.value = ''
}

function removeTag(tag) {
  emit('update:modelValue', tags.value.filter(t => t !== tag))
}

function handleBackspace() {
  if (!input.value && tags.value.length) {
    emit('update:modelValue', tags.value.slice(0, -1))
  }
}
</script>
