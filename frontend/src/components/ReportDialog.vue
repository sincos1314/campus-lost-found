<template>
  <el-dialog v-model="visible" title="举报" width="600px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="举报类别">
        <el-select v-model="form.category" placeholder="请选择">
          <el-option label="垃圾信息" value="spam" />
          <el-option label="骚扰/辱骂" value="abuse" />
          <el-option label="虚假信息" value="fake" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item label="严重级">
        <el-select v-model="form.severity" placeholder="请选择">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
        </el-select>
      </el-form-item>
      <el-form-item label="说明">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请填写详细说明"
        />
      </el-form-item>
      <el-form-item label="证据图片">
        <div class="image-upload-container">
          <div class="image-list" v-if="imageList.length > 0">
            <div
              v-for="(img, index) in imageList"
              :key="index"
              class="image-item"
            >
              <img :src="img.preview" class="thumbnail-image" />
              <div class="image-overlay">
                <el-button
                  type="danger"
                  size="small"
                  circle
                  :icon="Delete"
                  @click="removeImage(index)"
                  class="delete-btn"
                />
              </div>
              <div class="image-index">{{ index + 1 }}</div>
            </div>
          </div>
          <el-upload
            v-if="imageList.length < 8"
            class="image-uploader"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageChange"
            :multiple="true"
            accept="image/*"
          >
            <el-icon class="uploader-icon"><Plus /></el-icon>
          </el-upload>
        </div>
        <div class="upload-tip">
          <el-text type="info" size="small">
            支持 jpg、png、gif 格式，每张原始大小不超过10MB，上传前会自动压缩（保持较高质量），最多上传8张
          </el-text>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="uploadLoading" @click="submit">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits, computed } from "vue";
import { Plus, Delete } from "@element-plus/icons-vue";
import imageCompression from "browser-image-compression";
import request, { apiOrigin, absoluteUrl } from "../utils/request";
import { getToken } from "../utils/auth";
import { ElMessage } from "element-plus";

const props = defineProps({
  modelValue: Boolean,
  targetUserId: Number,
  itemId: Number,
});
const emit = defineEmits(["update:modelValue", "submitted"]);
const visible = ref(false);
const form = ref({ category: "spam", severity: "medium", description: "", anonymous: false });
const imageList = ref([]);
const token = getToken();
const uploadLoading = ref(false);

watch(
  () => props.modelValue,
  (v) => {
    visible.value = v;
    if (v) {
      // 重置表单和图片列表
      form.value = { category: "spam", severity: "medium", description: "", anonymous: false };
      imageList.value = [];
    }
  }
);
watch(visible, (v) => emit("update:modelValue", v));

const handleImageChange = async (file, fileList) => {
  // 检查是否已达到8张限制
  if (imageList.value.length >= 8) {
    ElMessage.warning('最多只能上传8张图片，请先删除部分图片后再上传')
    return false
  }

  const isImage = file.raw.type.startsWith('image/')
  const originalSizeMB = file.raw.size / 1024 / 1024

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  
  // 检查原始文件大小（最大 10MB）
  if (originalSizeMB > 10) {
    ElMessage.error('图片大小不能超过10MB！')
    return false
  }

  try {
    // 压缩图片（证据图片需要保持较高质量）
    const options = {
      maxSizeMB: 3, // 压缩后最大 3MB（比普通图片大，保持质量）
      maxWidthOrHeight: 2560, // 最大宽度或高度（更大，保持清晰度）
      useWebWorker: true,
      fileType: file.raw.type,
      initialQuality: 0.9 // 初始质量 90%（保持较高质量）
    }

    const loadingMessage = ElMessage({
      message: '正在压缩图片...',
      type: 'info',
      duration: 0
    })

    const compressedBlob = await imageCompression(file.raw, options)
    
    const originalName = file.raw.name || `image_${Date.now()}.jpg`
    const fileExtension = originalName.split('.').pop() || 'jpg'
    const fileName = originalName.replace(/\.[^/.]+$/, '') || 'image'
    const compressedFile = new File(
      [compressedBlob], 
      `${fileName}_compressed.${fileExtension}`, 
      { type: compressedBlob.type || file.raw.type }
    )
    
    loadingMessage.close()

    const compressedSizeMB = compressedFile.size / 1024 / 1024
    const compressionRatio = ((1 - compressedFile.size / file.raw.size) * 100).toFixed(1)
    
    if (compressionRatio > 20) {
      ElMessage.success(`图片已压缩：${originalSizeMB.toFixed(2)}MB → ${compressedSizeMB.toFixed(2)}MB (减少 ${compressionRatio}%)`)
    }

    // 检查总大小（8张 × 3MB = 24MB，留有余地设为 30MB）
    const currentTotalSize = imageList.value.reduce((sum, img) => sum + img.file.size, 0)
    const newTotalSize = currentTotalSize + compressedFile.size
    const maxTotalSize = 30 * 1024 * 1024 // 30MB

    if (newTotalSize > maxTotalSize) {
      const currentTotalMB = (currentTotalSize / 1024 / 1024).toFixed(2)
      ElMessage.error(`图片总大小不能超过30MB（压缩后）！当前已上传 ${currentTotalMB}MB，此图片 ${compressedSizeMB.toFixed(2)}MB`)
      return false
    }

    // 创建预览
    const reader = new FileReader()
    reader.onload = (e) => {
      if (imageList.value.length >= 8) {
        ElMessage.warning('最多只能上传8张图片')
        return
      }
      imageList.value.push({
        file: compressedFile,
        preview: e.target.result
      })
    }
    reader.readAsDataURL(compressedFile)
    
    return true
  } catch (error) {
    console.error('图片压缩失败:', error)
    ElMessage.error('图片压缩失败，请重试')
    return false
  }
}

const removeImage = (index) => {
  imageList.value.splice(index, 1)
}

const submit = async () => {
  if (imageList.value.length === 0) {
    // 没有图片，直接提交
    await request.post("/reports", {
      target_user_id: props.targetUserId,
      item_id: props.itemId,
      category: form.value.category,
      severity: form.value.severity,
      description: form.value.description,
      anonymous: form.value.anonymous,
    });
    ElMessage.success("举报已提交");
    emit("submitted");
    visible.value = false;
    return;
  }

  // 有图片，需要上传
  uploadLoading.value = true;
  try {
    const formData = new FormData();
    formData.append('target_user_id', props.targetUserId);
    formData.append('item_id', props.itemId);
    formData.append('category', form.value.category);
    formData.append('severity', form.value.severity);
    formData.append('description', form.value.description);
    formData.append('anonymous', form.value.anonymous ? 'true' : 'false');
    
    // 按顺序上传图片，第一张作为主图
    imageList.value.forEach((img, index) => {
      if (index === 0) {
        formData.append('image', img.file); // 主图
      } else {
        formData.append('images', img.file); // 副图
      }
    });

    await request.post("/reports", formData);
    
    ElMessage.success("证据图片上传成功，举报已提交");
    emit("submitted");
    visible.value = false;
  } catch (error) {
    console.error('提交失败:', error);
    ElMessage.error("提交失败，请重试");
  } finally {
    uploadLoading.value = false;
  }
};
</script>

<style scoped>
/* 对话框中的输入框样式 */
:deep(.el-dialog) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

:deep(.el-dialog .el-input),
:deep(.el-dialog .el-select),
:deep(.el-dialog .el-textarea) {
  border: none !important;
  box-shadow: none !important;
}

:deep(.el-dialog .el-input__wrapper),
:deep(.el-dialog .el-select__wrapper),
:deep(.el-dialog .el-textarea__inner) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

:deep(.el-dialog .el-input__inner),
:deep(.el-dialog .el-textarea__inner),
:deep(.el-dialog .el-select__placeholder),
:deep(.el-dialog .el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

:deep(.el-dialog .el-input__wrapper.is-focus),
:deep(.el-dialog .el-textarea__inner:focus),
:deep(.el-dialog .el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

:deep(.el-dialog .el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

:deep(.el-dialog .el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

:deep(.el-dialog .el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

/* 图片上传样式 */
.image-upload-container {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.image-item {
  position: relative;
  width: 120px;
  height: 120px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  overflow: hidden;
  transition: all 0.15s ease;
  background: var(--color-card);
}

.image-item:hover {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.delete-btn {
  background: rgba(245, 101, 101, 0.9);
  border: none;
}

.image-index {
  position: absolute;
  top: 4px;
  left: 4px;
  background: var(--color-accent);
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  border: 2px solid var(--color-card);
}

.image-uploader {
  width: 120px;
  height: 120px;
  border: var(--border-width) dashed var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  overflow: hidden;
  transition: all 0.15s ease;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-uploader:hover {
  border-color: var(--border-color);
  border-style: solid;
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.uploader-icon {
  font-size: 40px;
  color: #8c939d;
}

.upload-tip {
  margin-top: 10px;
}
</style>
