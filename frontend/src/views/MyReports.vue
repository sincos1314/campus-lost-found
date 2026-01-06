<template>
  <div class="my-reports-container">
    <el-card shadow="never">
      <template #header>
        <div class="header">
          <span>举报状态</span>
          <el-select
            v-model="status"
            placeholder="全部状态"
            size="small"
            @change="load"
          >
            <el-option label="全部" value="" />
            <el-option label="处理中" value="processing" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已举报" value="open" />
          </el-select>
        </div>
      </template>
      <el-empty v-if="reports.length === 0" description="暂无举报" />
      <el-table 
        v-else 
        :data="filtered" 
        :row-class-name="getRowClassName"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="举报类别" width="120">
          <template #default="{ row }">{{
            categoryText(row.category)
          }}</template>
        </el-table-column>
        <el-table-column label="严重级" width="100">
          <template #default="{ row }">{{
            severityText(row.severity)
          }}</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <span :class="{ 'withdrawn-text': row.status === 'withdrawn' }">
              {{ statusText(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
        <el-table-column label="被举报物品" width="220">
          <template #default="{ row }">
            <a
              v-if="row.item_id"
              @click="gotoItem(row.item_id)"
              class="item-link"
            >
              {{ row.item_title || "物品#" + row.item_id }}
            </a>
            <span v-else>无</span>
          </template>
        </el-table-column>
        <el-table-column label="证据" width="180">
          <template #default="{ row }">
            <div v-if="getEvidenceImages(row).length > 0" class="evidence-image-container">
              <el-image
                :src="absoluteUrl(getCurrentEvidenceImage(row))"
                :preview-src-list="getEvidencePreviewList(row)"
                style="width: 60px; height: 60px; z-index: 3000"
                :preview-teleported="true"
              />
              <div v-if="getEvidenceImages(row).length > 1" class="evidence-controls">
                <el-button
                  size="small"
                  circle
                  :disabled="getCurrentEvidenceIndex(row) === 0"
                  @click.stop="prevEvidenceImage(row)"
                  class="evidence-nav-btn"
                >
                  &lt;
                </el-button>
                <span class="evidence-counter">
                  {{ getCurrentEvidenceIndex(row) + 1 }}/{{ getEvidenceImages(row).length }}
                </span>
                <el-button
                  size="small"
                  circle
                  :disabled="getCurrentEvidenceIndex(row) === getEvidenceImages(row).length - 1"
                  @click.stop="nextEvidenceImage(row)"
                  class="evidence-nav-btn"
                >
                  &gt;
                </el-button>
              </div>
            </div>
            <span v-else>无</span>
          </template>
        </el-table-column>
        <el-table-column prop="resolution_note" label="处理备注" />
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" type="warning" @click="editReport(row)" :disabled="row.status==='withdrawn'">修改举报</el-button>
            <el-button size="small" type="danger" @click="withdrawReport(row)" :disabled="row.status==='withdrawn'">撤回举报</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-dialog v-model="editDialog" title="修改举报" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="举报类别">
          <el-select v-model="form.category">
            <el-option label="垃圾信息" value="spam" />
            <el-option label="骚扰/辱骂" value="abuse" />
            <el-option label="虚假信息" value="fake" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重级">
          <el-select v-model="form.severity">
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
            <div class="image-list" v-if="evidenceImageList.length > 0">
              <div
                v-for="(img, index) in evidenceImageList"
                :key="img.id || index"
                class="image-item"
              >
                <img :src="img.preview || img.url" class="thumbnail-image" />
                <div class="image-overlay">
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    :icon="Delete"
                    @click="removeEvidenceImage(index)"
                    class="delete-btn"
                  />
                </div>
                <div class="image-index">{{ index + 1 }}</div>
              </div>
            </div>
            <el-upload
              v-if="evidenceImageList.length < 8"
              class="image-uploader"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleEvidenceImageChange"
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
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Plus, Delete } from "@element-plus/icons-vue";
import imageCompression from "browser-image-compression";
import axios from "axios";
import request, { absoluteUrl, apiOrigin, previewList, previewListMultiple } from "../utils/request";
import { useRouter } from "vue-router";
import { getToken } from "../utils/auth";
import { ElMessage } from "element-plus";

const reports = ref([]);
const status = ref("");
// 存储每个举报的当前证据图片索引
const evidenceImageIndices = ref({});
const load = async () => {
  const all = await request.get("/my-reports");
  // enrich item title via additional fetch when needed
  for (const r of all) {
    if (r.item_id) {
      try {
        const it = await request.get(`/items/${r.item_id}`);
        r.item_title = it.title;
      } catch {}
    }
    // 确保 evidence_image_urls 是数组
    if (!r.evidence_image_urls || !Array.isArray(r.evidence_image_urls)) {
      if (r.evidence_image_url) {
        r.evidence_image_urls = [r.evidence_image_url];
      } else {
        r.evidence_image_urls = [];
      }
    }
    // 初始化图片索引（如果还没有）
    if (!evidenceImageIndices.value[r.id] && r.evidence_image_urls.length > 0) {
      evidenceImageIndices.value[r.id] = 0;
    }
  }
  reports.value = all;
};
const filtered = computed(() => {
  if (!status.value) return reports.value;
  return reports.value.filter((r) => r.status === status.value);
});
const router = useRouter();
const gotoItem = (id) => {
  router.push(`/item/${id}`);
};
const categoryText = (c) =>
  ({ spam: "垃圾信息", abuse: "骚扰/辱骂", fake: "虚假信息", other: "其他" }[
    c
  ] || c);
const severityText = (s) => ({ low: "低", medium: "中", high: "高" }[s] || s);
const statusText = (st) =>
  ({
    open: "已举报",
    processing: "管理员处理中",
    resolved: "已解决",
    rejected: "管理员已拒绝",
    withdrawn: "你已撤回举报",
  }[st] || st);
const editDialog = ref(false);
const form = ref({
  id: 0,
  category: "spam",
  severity: "medium",
  description: "",
  evidence_image_url: "",
  evidence_image_urls: [],
});
const evidenceImageList = ref([]); // 证据图片列表
const uploadQueue = ref([]); // 上传队列
const isUploading = ref(false); // 是否正在上传
const token = getToken();
const editReport = async (row) => {
  // 加载完整的举报信息
  try {
    const fullReport = await request.get(`/my-reports`);
    const report = fullReport.find(r => r.id === row.id);
    
    if (!report) {
      ElMessage.error('举报信息不存在')
      return
    }
    
    form.value = {
      id: row.id,
      category: row.category,
      severity: row.severity,
      description: row.description,
      evidence_image_url: report.evidence_image_url || '',
      evidence_image_urls: report.evidence_image_urls || []
    };
    
    // 初始化证据图片列表 - 确保从最新的后端数据加载
    evidenceImageList.value = [];
    
    // 优先使用 evidence_image_urls（多图）
    if (report.evidence_image_urls && Array.isArray(report.evidence_image_urls) && report.evidence_image_urls.length > 0) {
      evidenceImageList.value = report.evidence_image_urls.map((url, index) => {
        let filename = url
        if (url.startsWith('/api/image/')) {
          filename = url.replace('/api/image/', '')
        }
        return {
          id: `existing_${index}_${filename}`,
          url: url,
          preview: absoluteUrl(url),
          isExisting: true,
          originalUrl: url,
          filename: filename
        }
      })
    } 
    // 如果没有多图，使用单图（向后兼容）
    else if (report.evidence_image_url) {
      let filename = report.evidence_image_url
      if (filename.startsWith('/api/image/')) {
        filename = filename.replace('/api/image/', '')
      }
      evidenceImageList.value = [{
        id: `existing_0_${filename}`,
        url: report.evidence_image_url,
        preview: absoluteUrl(report.evidence_image_url),
        isExisting: true,
        originalUrl: report.evidence_image_url,
        filename: filename
      }]
    }
    
    // 清空上传队列
    uploadQueue.value = []
    isUploading.value = false
    
    editDialog.value = true;
  } catch (error) {
    console.error('加载举报详情失败:', error)
    ElMessage.error('加载失败')
  }
};
const submitEdit = async () => {
  // 等待所有上传完成
  while (isUploading.value || uploadQueue.value.length > 0) {
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  // 分离新图片和已存在的图片
  const newImages = evidenceImageList.value.filter(img => !img.isExisting)
  const existingImages = evidenceImageList.value.filter(img => img.isExisting)
  
  // 如果有图片变化，需要更新图片
  if (evidenceImageList.value.length > 0) {
    const formData = new FormData()
    
    // 使用 Set 来去重，避免重复添加相同的图片
    const keepExistingSet = new Set()
    
    // 添加要保留的已存在图片（按当前顺序）
    existingImages.forEach(img => {
      let imagePath = img.filename
      if (!imagePath) {
        imagePath = img.originalUrl || img.url
        if (imagePath.startsWith('/api/image/')) {
          imagePath = imagePath.replace('/api/image/', '')
        }
      }
      if (imagePath) {
        keepExistingSet.add(imagePath)
      }
    })
    
    // 添加已上传成功的新图片（有 filename 的新图片）
    newImages.forEach(img => {
      if (img.filename && img.filename.startsWith('evidence_')) {
        keepExistingSet.add(img.filename)
      }
    })
    
    // 将去重后的图片添加到 FormData（按列表顺序）
    // 先添加已存在的图片
    existingImages.forEach(img => {
      let imagePath = img.filename
      if (!imagePath) {
        imagePath = img.originalUrl || img.url
        if (imagePath.startsWith('/api/image/')) {
          imagePath = imagePath.replace('/api/image/', '')
        }
      }
      if (imagePath && keepExistingSet.has(imagePath)) {
        formData.append('keep_existing', imagePath)
        keepExistingSet.delete(imagePath) // 避免重复
      }
    })
    
    // 再添加已上传成功的新图片
    newImages.forEach(img => {
      if (img.filename && img.filename.startsWith('evidence_') && keepExistingSet.has(img.filename)) {
        formData.append('keep_existing', img.filename)
        keepExistingSet.delete(img.filename) // 避免重复
      }
    })
    
    // 添加还未上传的新图片（没有 filename 的）
    const pendingNewImages = newImages.filter(img => !img.filename || !img.filename.startsWith('evidence_'))
    pendingNewImages.forEach((img, index) => {
      const position = existingImages.length + (newImages.length - pendingNewImages.length) + index
      if (position === 0) {
        formData.append('image', img.file) // 主图
      } else {
        formData.append('images', img.file) // 副图
      }
    })
    
    // 更新图片 - 使用原生 axios 发送 FormData
    const token = getToken()
    const API_ORIGIN = apiOrigin || `http://${location.hostname}:5000`
    
    // 创建一个新的 axios 实例，确保不会受到任何拦截器影响
    const axiosInstance = axios.create({
      baseURL: API_ORIGIN,
      timeout: 30000
    })
    
    await axiosInstance.post(
      `/api/reports/${form.value.id}`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          // 完全不设置 Content-Type，让浏览器自动设置（包括 boundary）
        },
        // 确保 axios 不会自动设置 Content-Type
        transformRequest: [(data) => {
          // 如果是 FormData，直接返回，不进行任何转换
          return data
        }]
      }
    )
  } else {
    // 如果所有图片都被删除了，需要清空图片
    const formData = new FormData()
    const token = getToken()
    const API_ORIGIN = apiOrigin || `http://${location.hostname}:5000`
    
    // 创建一个新的 axios 实例
    const axiosInstance = axios.create({
      baseURL: API_ORIGIN,
      timeout: 30000
    })
    
    await axiosInstance.post(
      `/api/reports/${form.value.id}`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        transformRequest: [(data) => data]
      }
    )
  }
  
  // 更新其他信息
  await request.put(`/reports/${form.value.id}`, {
    category: form.value.category,
    severity: form.value.severity,
    description: form.value.description,
  });
  editDialog.value = false;
  await load();
  // 重置当前举报的图片索引
  if (evidenceImageIndices.value[form.value.id] !== undefined) {
    evidenceImageIndices.value[form.value.id] = 0;
  }
};

// 证据图片处理函数
const handleEvidenceImageChange = async (file, fileList) => {
  // 检查是否已达到8张限制
  if (evidenceImageList.value.length >= 8) {
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
    const currentTotalSize = evidenceImageList.value
      .filter(img => !img.isExisting && img.file)
      .reduce((sum, img) => sum + img.file.size, 0)
    const newTotalSize = currentTotalSize + compressedFile.size
    const maxTotalSize = 30 * 1024 * 1024 // 30MB

    if (newTotalSize > maxTotalSize) {
      const currentTotalMB = (currentTotalSize / 1024 / 1024).toFixed(2)
      ElMessage.error(`图片总大小不能超过30MB（压缩后）！当前已上传 ${currentTotalMB}MB，此图片 ${compressedSizeMB.toFixed(2)}MB`)
      return false
    }

    // 创建预览并加入上传队列
    const reader = new FileReader()
    reader.onload = async (e) => {
      if (evidenceImageList.value.length >= 8) {
        ElMessage.warning('最多只能上传8张图片')
        return
      }
      
      // 生成唯一ID，包含时间戳和随机数，确保唯一性
      const uniqueId = `new_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const newImage = {
        id: uniqueId,
        file: compressedFile,
        preview: e.target.result,
        isExisting: false,
        filename: null, // 上传成功后会被设置
        uploadTimestamp: Date.now(), // 记录上传时间，用于匹配
        fileSize: compressedFile.size, // 记录文件大小，用于精确匹配
        originalName: file.raw.name || `image_${Date.now()}.jpg` // 记录原始文件名
      }
      
      // 先添加到列表（显示预览）
      evidenceImageList.value.push(newImage)
      
      // 加入上传队列，按顺序上传
      uploadQueue.value.push(newImage)
      
      // 如果当前没有在上传，开始处理队列
      if (!isUploading.value) {
        processUploadQueue()
      }
    }
    reader.readAsDataURL(compressedFile)
    
    return true
  } catch (error) {
    console.error('图片压缩失败:', error)
    ElMessage.error('图片压缩失败，请重试')
    return false
  }
}

// 处理上传队列（按顺序上传，避免并发问题）
const processUploadQueue = async () => {
  if (isUploading.value || uploadQueue.value.length === 0) {
    return
  }
  
  isUploading.value = true
  
  while (uploadQueue.value.length > 0) {
    const imageItem = uploadQueue.value.shift() // 从队列中取出第一张
    
    try {
      await uploadEvidenceImage(imageItem)
    } catch (err) {
      console.error('上传失败:', err)
      // 上传失败，从列表中移除
      const index = evidenceImageList.value.findIndex(img => img.id === imageItem.id)
      if (index > -1) {
        evidenceImageList.value.splice(index, 1)
      }
    }
  }
  
  isUploading.value = false
}

// 实时上传单张图片
const uploadEvidenceImage = async (imageItem) => {
  try {
    const formData = new FormData()
    
    // 使用 Set 来去重，避免重复添加相同的图片
    const keepExistingSet = new Set()
    
    // 添加要保留的已存在图片
    const existingImages = evidenceImageList.value.filter(img => img.isExisting)
    existingImages.forEach(img => {
      let imagePath = img.filename
      if (!imagePath) {
        imagePath = img.originalUrl || img.url
        if (imagePath.startsWith('/api/image/')) {
          imagePath = imagePath.replace('/api/image/', '')
        }
      }
      if (imagePath) {
        keepExistingSet.add(imagePath)
      }
    })
    
    // 添加所有已上传成功的新图片（有 filename 的图片，排除当前正在上传的）
    // 这些图片已经在之前的上传中保存到服务器，现在需要保留
    const uploadedNewImages = evidenceImageList.value.filter(img => 
      img.id !== imageItem.id && img.filename && img.filename.startsWith('evidence_')
    )
    uploadedNewImages.forEach(img => {
      if (img.filename) {
        keepExistingSet.add(img.filename)
      }
    })
    
    // 将去重后的图片添加到 FormData
    keepExistingSet.forEach(filename => {
      formData.append('keep_existing', filename)
    })
    
    // 添加当前正在上传的新图片
    const newImages = evidenceImageList.value.filter(img => !img.isExisting)
    const imageIndex = newImages.findIndex(img => img.id === imageItem.id)
    const position = existingImages.length + uploadedNewImages.length + imageIndex
    
    if (position === 0) {
      formData.append('image', imageItem.file) // 主图
    } else {
      formData.append('images', imageItem.file) // 副图
    }
    
    // 使用原生 axios 发送 FormData，确保 Content-Type 正确
    const token = getToken()
    const API_ORIGIN = apiOrigin || `http://${location.hostname}:5000`
    
    console.log('[DEBUG] 准备上传图片，FormData 内容:')
    for (let pair of formData.entries()) {
      console.log('[DEBUG]', pair[0], pair[1] instanceof File ? `File: ${pair[1].name}` : pair[1])
    }
    
    // 创建一个新的 axios 实例，确保不会受到任何拦截器影响
    const axiosInstance = axios.create({
      baseURL: API_ORIGIN,
      timeout: 30000
    })
    
    // 使用原生 axios 发送，不通过封装的 request，避免拦截器问题
    const response = await axiosInstance.post(
      `/api/reports/${form.value.id}`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          // 完全不设置 Content-Type，让浏览器自动设置（包括 boundary）
        },
        // 确保 axios 不会自动设置 Content-Type
        transformRequest: [(data) => {
          // 如果是 FormData，直接返回，不进行任何转换
          return data
        }]
      }
    )
    
    // 上传成功后，更新当前图片的状态，但不重建整个列表（避免覆盖其他正在上传的图片）
    if (response.data && response.data.message === 'updated') {
      // 重新获取最新的举报数据，找到刚上传的图片
      const updated = await request.get(`/my-reports`)
      const report = updated.find(r => r.id === form.value.id)
      if (report) {
        // 确保 evidence_image_urls 是数组
        let allUrls = []
        if (report.evidence_image_urls && Array.isArray(report.evidence_image_urls) && report.evidence_image_urls.length > 0) {
          allUrls = report.evidence_image_urls
        } else if (report.evidence_image_url) {
          allUrls = [report.evidence_image_url]
        }
        
        // 获取所有已存在的图片的 filename（包括已上传成功的新图片）
        const existingFilenames = new Set()
        evidenceImageList.value.forEach(img => {
          if (img.filename) {
            existingFilenames.add(img.filename)
          }
        })
        
        // 找到新上传的图片（不在已存在图片列表中的）
        const newUploadedUrls = allUrls.filter(url => {
          let filename = url
          if (url.startsWith('/api/image/')) {
            filename = url.replace('/api/image/', '')
          }
          return !existingFilenames.has(filename)
        })
        
        // 如果找到了新上传的图片，使用时间戳精确匹配
        if (newUploadedUrls.length > 0) {
          const currentTimestamp = imageItem.uploadTimestamp || Date.now()
          
          // 按时间戳排序，找到最接近当前上传时间的图片
          const sortedUrls = newUploadedUrls.map(url => {
            const filename = url.startsWith('/api/image/') ? url.replace('/api/image/', '') : url
            const match = filename.match(/evidence_(\d+\.\d+)_/)
            const urlTimestamp = match ? parseFloat(match[1]) * 1000 : 0
            return {
              url,
              filename,
              timestamp: urlTimestamp,
              timeDiff: Math.abs(urlTimestamp - currentTimestamp)
            }
          }).sort((a, b) => a.timeDiff - b.timeDiff) // 按时间差排序
          
          // 使用时间戳最接近的图片（时间差小于5秒）
          let uploadedUrl = null
          if (sortedUrls.length > 0 && sortedUrls[0].timeDiff < 5000) {
            uploadedUrl = sortedUrls[0].url
          } else if (sortedUrls.length > 0) {
            // 如果时间差太大，使用第一张（可能是唯一的新图片）
            uploadedUrl = sortedUrls[0].url
          }
          
          if (uploadedUrl) {
            let filename = uploadedUrl
            if (uploadedUrl.startsWith('/api/image/')) {
              filename = uploadedUrl.replace('/api/image/', '')
            }
            
            // 更新当前图片项的状态
            imageItem.isExisting = true
            imageItem.url = uploadedUrl
            imageItem.originalUrl = uploadedUrl
            imageItem.filename = filename  // 关键：设置 filename，这样下次上传时就能识别它
            imageItem.preview = absoluteUrl(uploadedUrl)
            
            console.log(`[DEBUG] 图片匹配成功: ${imageItem.originalName} -> ${filename} (时间差: ${sortedUrls[0]?.timeDiff || 0}ms)`)
          } else {
            console.warn(`[DEBUG] 图片匹配失败: ${imageItem.originalName}, 新上传的图片数量: ${newUploadedUrls.length}`)
          }
        } else {
          console.warn(`[DEBUG] 没有找到新上传的图片: ${imageItem.originalName}`)
        }
        
        // 同时更新列表中所有已存在图片的 URL（以防后端顺序有变化）
        evidenceImageList.value.forEach(img => {
          if (img.isExisting && img.filename) {
            const matchingUrl = allUrls.find(url => {
              const urlFilename = url.startsWith('/api/image/') ? url.replace('/api/image/', '') : url
              return urlFilename === img.filename
            })
            if (matchingUrl) {
              img.url = matchingUrl
              img.originalUrl = matchingUrl
              img.preview = absoluteUrl(matchingUrl)
            }
          }
        })
      }
      ElMessage.success('图片上传成功')
    } else {
      ElMessage.success('图片上传成功')
    }
  } catch (error) {
    console.error('图片上传失败:', error)
    ElMessage.error('图片上传失败，请重试')
    // 上传失败，从列表中移除
    const index = evidenceImageList.value.findIndex(img => img.id === imageItem.id)
    if (index > -1) {
      evidenceImageList.value.splice(index, 1)
    }
  }
}

const removeEvidenceImage = async (index) => {
  const imageItem = evidenceImageList.value[index]
  evidenceImageList.value.splice(index, 1)
  
  // 如果删除的是已存在的图片，需要更新后端
  if (imageItem.isExisting) {
    try {
      const formData = new FormData()
      
      // 使用 Set 来去重，避免重复添加相同的图片
      const keepExistingSet = new Set()
      
      // 添加要保留的已存在图片（按当前顺序）
      const existingImages = evidenceImageList.value.filter(img => img.isExisting)
      existingImages.forEach(img => {
        let imagePath = img.filename
        if (!imagePath) {
          imagePath = img.originalUrl || img.url
          if (imagePath.startsWith('/api/image/')) {
            imagePath = imagePath.replace('/api/image/', '')
          }
        }
        if (imagePath) {
          keepExistingSet.add(imagePath)
        }
      })
      
      // 添加已上传成功的新图片（有 filename 的图片，无论 isExisting 状态）
      const uploadedNewImages = evidenceImageList.value.filter(img => 
        img.filename && img.filename.startsWith('evidence_')
      )
      uploadedNewImages.forEach(img => {
        if (img.filename) {
          keepExistingSet.add(img.filename)
        }
      })
      
      // 将去重后的图片添加到 FormData
      keepExistingSet.forEach(filename => {
        formData.append('keep_existing', filename)
      })
      
      // 添加还未上传的新图片（没有 filename 的）
      const pendingNewImages = evidenceImageList.value.filter(img => 
        !img.filename || !img.filename.startsWith('evidence_')
      )
      // 排除已存在的图片
      const newPendingImages = pendingNewImages.filter(img => !img.isExisting)
      newPendingImages.forEach((img, idx) => {
        const position = existingImages.length + uploadedNewImages.length + idx
        if (position === 0) {
          formData.append('image', img.file)
        } else {
          formData.append('images', img.file)
        }
      })
      
      const token = getToken()
      const API_ORIGIN = apiOrigin || `http://${location.hostname}:5000`
      
      // 创建一个新的 axios 实例
      const axiosInstance = axios.create({
        baseURL: API_ORIGIN,
        timeout: 30000
      })
      
      await axiosInstance.post(
        `/api/reports/${form.value.id}`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
          transformRequest: [(data) => data]
        }
      )
      
      ElMessage.success('图片已删除')
    } catch (error) {
      console.error('删除图片失败:', error)
      ElMessage.error('删除失败，请重试')
      // 恢复图片
      evidenceImageList.value.splice(index, 0, imageItem)
    }
  }
}
const withdrawReport = async (row) => {
  await request.put(`/reports/${row.id}`, { withdraw: true });
  await load();
};

// 为表格行添加类名，用于样式控制
const getRowClassName = ({ row }) => {
  return row.status === 'withdrawn' ? 'withdrawn-row' : '';
};

// 获取举报的所有证据图片
const getEvidenceImages = (row) => {
  if (row.evidence_image_urls && Array.isArray(row.evidence_image_urls) && row.evidence_image_urls.length > 0) {
    return row.evidence_image_urls;
  } else if (row.evidence_image_url) {
    return [row.evidence_image_url];
  }
  return [];
};

// 获取当前显示的证据图片
const getCurrentEvidenceImage = (row) => {
  const images = getEvidenceImages(row);
  if (images.length === 0) return '';
  const index = getCurrentEvidenceIndex(row);
  return images[index] || images[0];
};

// 获取当前证据图片索引
const getCurrentEvidenceIndex = (row) => {
  if (!evidenceImageIndices.value[row.id]) {
    evidenceImageIndices.value[row.id] = 0;
  }
  return evidenceImageIndices.value[row.id];
};

// 获取证据图片预览列表
const getEvidencePreviewList = (row) => {
  const images = getEvidenceImages(row);
  return previewListMultiple(images);
};

// 上一张证据图片
const prevEvidenceImage = (row) => {
  const images = getEvidenceImages(row);
  if (images.length <= 1) return;
  const currentIndex = getCurrentEvidenceIndex(row);
  if (currentIndex > 0) {
    evidenceImageIndices.value[row.id] = currentIndex - 1;
  }
};

// 下一张证据图片
const nextEvidenceImage = (row) => {
  const images = getEvidenceImages(row);
  if (images.length <= 1) return;
  const currentIndex = getCurrentEvidenceIndex(row);
  if (currentIndex < images.length - 1) {
    evidenceImageIndices.value[row.id] = currentIndex + 1;
  }
};

onMounted(load);
</script>

<style scoped>
.my-reports-container {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.my-reports-container :deep(.el-card) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.my-reports-container :deep(.el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 700;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.my-reports-container :deep(.el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

.my-reports-container :deep(.el-button--primary:hover) {
  background: var(--color-accent) !important;
  color: white !important;
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.my-reports-container :deep(.el-button--warning) {
  background: #ed8936;
  color: white !important;
}

.my-reports-container :deep(.el-button--warning:hover) {
  background: #ed8936 !important;
  color: white !important;
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.my-reports-container :deep(.el-button--danger) {
  background: #f56565;
  color: white !important;
}

.my-reports-container :deep(.el-button--danger:hover) {
  background: #f56565 !important;
  color: white !important;
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

/* 移除 Element Plus 默认的输入框包装器样式 */
.my-reports-container :deep(.el-input),
.my-reports-container :deep(.el-select),
.my-reports-container :deep(.el-textarea) {
  border: none !important;
  box-shadow: none !important;
}

.my-reports-container :deep(.el-input__wrapper),
.my-reports-container :deep(.el-select__wrapper),
.my-reports-container :deep(.el-textarea__inner) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

.my-reports-container :deep(.el-input__inner),
.my-reports-container :deep(.el-textarea__inner),
.my-reports-container :deep(.el-select__placeholder),
.my-reports-container :deep(.el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.my-reports-container :deep(.el-input__wrapper.is-focus),
.my-reports-container :deep(.el-textarea__inner:focus),
.my-reports-container :deep(.el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

.my-reports-container :deep(.el-table) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
}

.my-reports-container :deep(.el-table th) {
  background: var(--color-primary);
  color: var(--color-text);
  font-weight: 900;
  font-size: 0.95rem;
}

.my-reports-container :deep(.el-table td) {
  font-weight: 600;
  color: var(--color-text);
}

/* 已撤回举报的行样式 */
.my-reports-container :deep(.el-table .withdrawn-row) {
  background-color: rgba(0, 0, 0, 0.08) !important;
  opacity: 0.65;
  position: relative;
}

.my-reports-container :deep(.el-table .withdrawn-row:hover) {
  background-color: rgba(0, 0, 0, 0.1) !important;
}

.my-reports-container :deep(.el-table .withdrawn-row td) {
  color: var(--muted) !important;
}

/* 已撤回举报文字样式 */
.withdrawn-text {
  color: #f56565 !important;
  font-weight: 900 !important;
}

/* 对话框中的输入框样式 */
.my-reports-container :deep(.el-dialog) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.my-reports-container :deep(.el-dialog .el-input),
.my-reports-container :deep(.el-dialog .el-select),
.my-reports-container :deep(.el-dialog .el-textarea) {
  border: none !important;
  box-shadow: none !important;
}

.my-reports-container :deep(.el-dialog .el-input__wrapper),
.my-reports-container :deep(.el-dialog .el-select__wrapper),
.my-reports-container :deep(.el-dialog .el-textarea__inner) {
  border: var(--border-width) solid var(--border-color) !important;
  border-radius: var(--border-radius) !important;
  background: var(--color-card) !important;
  box-shadow: none !important;
  padding: 0.6rem 1rem !important;
}

.my-reports-container :deep(.el-dialog .el-input__inner),
.my-reports-container :deep(.el-dialog .el-select__placeholder),
.my-reports-container :deep(.el-dialog .el-select__selected-item) {
  border: none !important;
  background: transparent !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

/* textarea 的 inner 不应该在这里设置 border: none，因为我们需要边框 */
.my-reports-container :deep(.el-dialog .el-textarea__inner) {
  /* 不设置 border: none，保持之前设置的边框样式 */
  background: var(--color-card) !important;
  color: var(--color-text) !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
}

.my-reports-container :deep(.el-dialog .el-input__wrapper.is-focus),
.my-reports-container :deep(.el-dialog .el-textarea__inner:focus),
.my-reports-container :deep(.el-dialog .el-select__wrapper.is-focused) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
}

/* 确保 textarea 的 focus 状态也有阴影效果 */
.my-reports-container :deep(.el-dialog .el-textarea__inner:focus) {
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color) !important;
  border-color: var(--border-color) !important;
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

/* 证据图片容器样式 */
.evidence-image-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.evidence-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.evidence-nav-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  font-size: 14px;
  font-weight: 700;
  border: var(--border-width) solid var(--border-color);
  border-radius: 50%;
  background: var(--color-card);
  color: var(--color-text);
  transition: all 0.15s ease;
}

.evidence-nav-btn:hover:not(:disabled) {
  background: var(--color-accent);
  color: white;
  transform: translateY(-2px);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.evidence-nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.evidence-counter {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text);
  min-width: 40px;
  text-align: center;
}

/* 确保图片预览不被遮挡 */
.my-reports-container :deep(.el-image-viewer__wrapper) {
  z-index: 9999 !important;
}

.my-reports-container :deep(.el-image-viewer__mask) {
  z-index: 9998 !important;
}

/* 被举报物品链接样式 - 去掉边框和阴影 */
.my-reports-container .item-link {
  color: var(--color-accent);
  text-decoration: none;
  cursor: pointer;
  border: none;
  background: transparent;
  box-shadow: none;
  padding: 0;
  font-weight: 400;
}

.my-reports-container .item-link:hover {
  color: var(--color-accent);
  text-decoration: underline;
  border: none;
  box-shadow: none;
  background: transparent;
}
</style>
