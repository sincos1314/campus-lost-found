<template>
  <div class="item-detail-container">
    <!-- 返回按钮 -->
    <el-button class="back-button" @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      返回列表
    </el-button>

    <el-card class="detail-card" v-loading="loading">
      <el-row :gutter="40">
        <!-- 左侧：图片 -->
        <el-col :xs="24" :sm="24" :md="10">
          <div class="image-section">
            <!-- 多张图片显示 -->
            <div v-if="imageUrls && imageUrls.length > 0" class="images-container">
              <el-image
                :src="absoluteUrl(imageUrls[currentMainImageIndex])"
                :preview-src-list="previewImageUrls"
                fit="cover"
                class="item-image main-image"
              >
                <template #error>
                  <div class="image-placeholder">
                    <el-icon :size="60"><Picture /></el-icon>
                    <p>图片加载失败</p>
                  </div>
                </template>
              </el-image>
              <!-- 多张图片缩略图 -->
              <div v-if="imageUrls.length > 1" class="thumbnail-list">
                <div
                  v-for="(url, index) in imageUrls"
                  :key="index"
                  class="thumbnail-item"
                  :class="{ active: index === currentMainImageIndex }"
                  @click="switchMainImage(index)"
                >
                  <el-image
                    :src="absoluteUrl(url)"
                    fit="cover"
                    class="thumbnail-image"
                  />
                  <div class="thumbnail-overlay">{{ index + 1 }}</div>
                </div>
              </div>
            </div>
            <!-- 单张图片或没有图片 -->
            <div v-else>
              <el-image
                v-if="item.image_url"
                :src="fullImageUrl"
                :preview-src-list="previewList(item.image_url)"
                fit="cover"
                class="item-image"
              >
                <template #error>
                  <div class="image-placeholder">
                    <el-icon :size="60"><Picture /></el-icon>
                    <p>暂无图片</p>
                  </div>
                </template>
              </el-image>
              <div v-else class="image-placeholder">
                <el-icon :size="60"><Picture /></el-icon>
                <p>暂无图片</p>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右侧：详细信息 -->
        <el-col :xs="24" :sm="24" :md="14">
          <div class="info-section">
            <!-- 标题和标签 -->
            <div class="title-section">
              <h2>{{ item.title }}</h2>
              <div class="tags">
                <el-tag
                  :type="item.category === 'lost' ? 'danger' : 'success'"
                  size="large"
                >
                  {{ item.category === "lost" ? "失物" : "拾物" }}
                </el-tag>
                <el-tag
                  :type="item.status === 'open' ? 'info' : 'warning'"
                  size="large"
                >
                  {{ item.status === "open" ? "进行中" : "已解决" }}
                </el-tag>
              </div>
            </div>

            <!-- 详细信息表格 -->
            <el-descriptions :column="1" border class="info-table">
              <el-descriptions-item label="物品类型">
                {{ item.item_type }}
              </el-descriptions-item>
              <el-descriptions-item label="地点">
                <el-icon><Location /></el-icon>
                {{ item.location }}
              </el-descriptions-item>
              <el-descriptions-item label="日期">
                <el-icon><Calendar /></el-icon>
                {{ item.date }}
              </el-descriptions-item>
              <el-descriptions-item label="发布时间">
                <el-icon><Clock /></el-icon>
                {{ item.created_at }}
              </el-descriptions-item>
              <el-descriptions-item label="发布人">
                <el-button type="text" @click="viewPublisher">
                  <el-icon><User /></el-icon>
                  {{ item.username }}
                </el-button>
              </el-descriptions-item>
            </el-descriptions>

            <!-- 详细描述 -->
            <div class="description-section">
              <h3>详细描述</h3>
              <p class="description-text">{{ item.description }}</p>
            </div>

            <div class="timeline-section">
              <h3>时间线</h3>
              <el-timeline>
                <el-timeline-item
                  v-for="(ev, i) in filteredTimeline"
                  :key="i"
                  :timestamp="ev.time"
                  :type="ev.type === 'success' ? 'success' : 'primary'"
                >
                  <div class="timeline-title">{{ ev.title }}</div>
                  <div class="timeline-desc">{{ ev.description }}</div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- 联系方式 -->
            <div class="contact-section">
              <h3>联系方式</h3>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="联系人">
                  {{ item.contact_name }}
                </el-descriptions-item>
                <el-descriptions-item label="联系电话">
                  <span class="phone-number">{{ item.contact_phone }}</span>
                  <el-button
                    type="primary"
                    size="small"
                    :icon="CopyDocument"
                    @click="copyPhone"
                    style="margin-left: 10px"
                  >
                    复制
                  </el-button>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 操作按钮 -->
            <div class="action-section">
              <!-- 收藏按钮 -->
              <el-button
                v-if="isLoggedIn()"
                :type="isFavorited ? 'warning' : 'default'"
                size="large"
                @click="toggleFavorite"
              >
                <el-icon><Star /></el-icon>
                {{ isFavorited ? '已收藏' : '收藏' }}
              </el-button>

              <!-- 新增：联系发布者按钮（非本人发布时显示） -->
              <el-button
                v-if="isLoggedIn() && item.user_id !== getCurrentUserId()"
                type="primary"
                size="large"
                @click="contactPublisher"
              >
                <el-icon><ChatDotRound /></el-icon>
                联系发布者
              </el-button>

              <!-- 认领按钮（非本人发布且状态为进行中时显示） -->
              <el-button
                v-if="isLoggedIn() && item.user_id !== getCurrentUserId() && item.status === 'open'"
                type="success"
                size="large"
                @click="openClaimDialog"
              >
                <el-icon><Trophy /></el-icon>
                认领
              </el-button>

              <!-- 本人发布时显示管理按钮 -->
              <template
                v-if="isLoggedIn() && item.user_id === getCurrentUserId()"
              >
                <el-button
                  v-if="item.status === 'open'"
                  type="success"
                  size="large"
                  @click="markAsSolved"
                >
                  <el-icon><Check /></el-icon>
                  标记为已解决
                </el-button>
                <el-button type="danger" size="large" @click="deleteItem">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
              <el-button type="info" size="large" @click="openShare"
                >分享链接</el-button
              >
              <el-button type="warning" size="large" @click="openReport"
                >举报</el-button
              >
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
    <el-dialog v-model="shareVisible" title="分享二维码" width="320px">
      <div class="qr-box">
        <el-image
          :src="qrUrl"
          fit="contain"
          style="width: 260px; height: 260px"
        />
      </div>
      <template #footer>
        <el-button @click="copyLink">复制链接</el-button>
        <el-button type="primary" @click="shareVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    <ReportDialog
      v-model="reportVisible"
      :target-user-id="item.user_id"
      :item-id="itemId"
      @submitted="onReported"
    />

    <!-- 匹配推荐区域 -->
    <el-card class="matches-card" v-if="matchedItems.length > 0">
      <template #header>
        <div class="card-header">
          <el-icon><Connection /></el-icon>
          <span>可能匹配的物品</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col
          v-for="match in matchedItems"
          :key="match.id"
          :xs="24"
          :sm="12"
          :md="8"
        >
          <div class="match-item-wrapper" @click="() => goToItem(match.id)">
            <el-card
              class="match-item-card"
              shadow="hover"
            >
              <div class="match-item-image-wrapper">
                <el-image
                  v-if="match.image_url"
                  :src="absoluteUrl(match.image_url)"
                  fit="cover"
                  class="match-item-image"
                />
                <div v-else class="match-item-placeholder">
                  <el-icon><Picture /></el-icon>
                </div>
              </div>
              <div class="match-item-info">
                <h4>{{ match.title }}</h4>
                <p class="match-item-location">
                  <el-icon><Location /></el-icon>
                  {{ match.location }}
                </p>
                <el-tag
                  :type="match.category === 'lost' ? 'danger' : 'success'"
                  size="small"
                >
                  {{ match.category === 'lost' ? '失物' : '拾物' }}
                </el-tag>
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 认领列表区域（仅发布者可见） -->
    <el-card class="claims-card" v-if="isLoggedIn() && item.user_id === getCurrentUserId() && claims.length > 0">
      <template #header>
        <div class="card-header">
          <el-icon><Trophy /></el-icon>
          <span>认领申请 ({{ claims.length }})</span>
        </div>
      </template>
      <div class="claims-list">
        <div
          v-for="claim in claims"
          :key="claim.id"
          class="claim-item"
        >
          <div class="claim-header">
            <div class="claim-user-info">
              <span class="claim-username">{{ claim.claimant_username }}</span>
              <span class="claim-time">{{ formatTime(claim.created_at) }}</span>
            </div>
            <el-tag
              :type="claim.status === 'approved' ? 'success' : claim.status === 'rejected' ? 'danger' : 'warning'"
              size="small"
            >
              {{ claim.status === 'approved' ? '已批准' : claim.status === 'rejected' ? '已拒绝' : '待处理' }}
            </el-tag>
          </div>
          <div class="claim-description">
            {{ claim.description }}
          </div>
          <!-- 认领证据图片 -->
          <div v-if="claim.image_urls && claim.image_urls.length > 0" class="claim-images">
            <div class="claim-images-grid">
              <el-image
                v-for="(imageUrl, index) in claim.image_urls"
                :key="index"
                :src="absoluteUrl(imageUrl)"
                :preview-src-list="claim.image_urls.map(url => absoluteUrl(url))"
                :initial-index="index"
                fit="cover"
                class="claim-image-item"
                :preview-teleported="true"
              />
            </div>
          </div>
          <div class="claim-actions" v-if="claim.status === 'pending'">
            <el-button
              type="success"
              size="small"
              @click="approveClaim(claim.id)"
            >
              批准
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="rejectClaim(claim.id)"
            >
              拒绝
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="contactClaimant(claim.claimant_id)"
            >
              <el-icon><ChatDotRound /></el-icon>
              联系申请认领者
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 评论区域 - YouTube风格 -->
    <el-card class="comments-card">
      <template #header>
        <div class="card-header">
          <el-icon><ChatLineRound /></el-icon>
          <span>评论 ({{ comments.length }})</span>
        </div>
      </template>

      <!-- 评论输入框 -->
      <div v-if="isLoggedIn()" class="comment-input-section youtube-style">
        <div class="comment-input-content">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="1"
            placeholder="添加公开评论..."
            maxlength="500"
            :autosize="{ minRows: 1, maxRows: 4 }"
            class="youtube-comment-input"
          />
          <div class="comment-input-actions">
            <el-button
              text
              @click="newComment = ''"
              :disabled="!newComment.trim()"
            >
              取消
            </el-button>
            <el-button
              type="primary"
              @click="submitComment"
              :disabled="!newComment.trim()"
              class="comment-submit-btn"
            >
              评论
            </el-button>
          </div>
        </div>
      </div>
      <div v-else class="comment-login-tip">
        <el-button type="primary" @click="router.push('/login')">
          登录后发表评论
        </el-button>
      </div>

      <!-- 评论列表 -->
      <div class="comments-list" v-if="comments.length > 0">
        <div
          v-for="comment in comments"
          :key="comment.id"
          class="comment-item"
        >
          <!-- 一级评论：用户名 时间 -->
          <div class="comment-header">
            <span class="comment-author">{{ comment.username }}</span>
            <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          </div>
          
          <!-- 评论内容 -->
          <div class="comment-content">{{ comment.content }}</div>

          <!-- 操作按钮 -->
          <div class="comment-actions">
            <el-button
              text
              size="small"
              @click="toggleReplyInput(comment.id)"
              v-if="isLoggedIn()"
            >
              回复
            </el-button>
            <el-button
              v-if="comment.user_id === getCurrentUserId()"
              text
              size="small"
              @click="editComment(comment)"
            >
              编辑
            </el-button>
            <el-button
              v-if="comment.user_id === getCurrentUserId()"
              text
              size="small"
              @click="deleteComment(comment.id)"
            >
              删除
            </el-button>
          </div>

          <!-- 回复输入框（回复一级评论） -->
          <div v-if="replyingTo === comment.id && isLoggedIn()" class="reply-input-box">
            <el-input
              v-model="replyContent"
              type="textarea"
              :rows="2"
              placeholder="添加回复..."
              maxlength="500"
            />
            <div class="reply-input-actions">
              <el-button text @click="cancelReply">取消</el-button>
              <el-button type="primary" @click="submitReply(comment.id, comment.user_id)" :disabled="!replyContent.trim()">
                回复
              </el-button>
            </div>
          </div>

          <!-- 回复列表（一级回复） -->
          <div v-if="comment.replies && comment.replies.length > 0" class="replies-section">
            <button
              class="toggle-replies-btn"
              @click="toggleReplies(comment.id)"
            >
              <el-icon>
                <ArrowDown v-if="!expandedReplies.has(comment.id)" />
                <ArrowUp v-else />
              </el-icon>
              <span>{{ comment.replies_count }} 条回复</span>
            </button>

            <div v-if="expandedReplies.has(comment.id)" class="replies-list">
              <!-- 一级回复：用户名：回复内容 时间 -->
              <div
                v-for="reply in getLevel1Replies(comment.replies)"
                :key="reply.id"
                class="reply-item level-1"
              >
                <div class="reply-line">
                  <span class="reply-author">{{ reply.username }}</span>
                  <span class="reply-separator">：</span>
                  <span class="reply-content">{{ reply.content }}</span>
                  <span class="reply-time">{{ formatTime(reply.created_at) }}</span>
                </div>
                
                <!-- 操作按钮 -->
                <div class="reply-actions">
                  <el-button
                    text
                    size="small"
                    @click="toggleReplyInput(reply.id, reply.user_id)"
                    v-if="isLoggedIn()"
                  >
                    回复
                  </el-button>
                  <el-button
                    v-if="reply.user_id === getCurrentUserId()"
                    text
                    size="small"
                    @click="editComment(reply)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    v-if="reply.user_id === getCurrentUserId()"
                    text
                    size="small"
                    @click="deleteComment(reply.id)"
                  >
                    删除
                  </el-button>
                </div>

                <!-- 回复一级回复的输入框 -->
                <div v-if="replyingTo === reply.id && isLoggedIn()" class="reply-input-box">
                  <el-input
                    v-model="replyContent"
                    type="textarea"
                    :rows="2"
                    placeholder="添加回复..."
                    maxlength="500"
                  />
                  <div class="reply-input-actions">
                    <el-button text @click="cancelReply">取消</el-button>
                    <el-button type="primary" @click="submitReply(reply.id, reply.user_id)" :disabled="!replyContent.trim()">
                      回复
                    </el-button>
                  </div>
                </div>

                <!-- 二级回复列表（不需要折叠） -->
                <div v-if="reply.level2_replies && reply.level2_replies.length > 0" class="level-2-replies">
                  <div
                    v-for="level2Reply in reply.level2_replies"
                    :key="level2Reply.id"
                    class="reply-item level-2"
                  >
                    <!-- 二级回复格式：用户A 回复 用户B：回复内容 时间 或 自己的用户名：回复内容 时间 -->
                    <div class="reply-line">
                      <span class="reply-author">{{ level2Reply.username }}</span>
                      <!-- 二级回复：如果有reply_to_username且不是自己回复自己，显示"回复 用户名" -->
                      <template v-if="level2Reply.reply_to_user_id && level2Reply.reply_to_user_id !== level2Reply.user_id">
                        <span class="reply-to-text">
                          回复
                          <span class="reply-target">{{ level2Reply.reply_to_username || '用户' }}</span>
                        </span>
                      </template>
                      <span class="reply-separator">：</span>
                      <span class="reply-content">{{ level2Reply.content }}</span>
                      <span class="reply-time">{{ formatTime(level2Reply.created_at) }}</span>
                    </div>
                    
                    <!-- 操作按钮 -->
                    <div class="reply-actions">
                      <el-button
                        text
                        size="small"
                        @click="toggleReplyInput(level2Reply.id, level2Reply.user_id)"
                        v-if="isLoggedIn()"
                      >
                        回复
                      </el-button>
                      <el-button
                        v-if="level2Reply.user_id === getCurrentUserId()"
                        text
                        size="small"
                        @click="editComment(level2Reply)"
                      >
                        编辑
                      </el-button>
                      <el-button
                        v-if="level2Reply.user_id === getCurrentUserId()"
                        text
                        size="small"
                        @click="deleteComment(level2Reply.id)"
                      >
                        删除
                      </el-button>
                    </div>

                    <!-- 回复二级回复的输入框 -->
                    <div v-if="replyingTo === level2Reply.id && isLoggedIn()" class="reply-input-box">
                      <el-input
                        v-model="replyContent"
                        type="textarea"
                        :rows="2"
                        placeholder="添加回复..."
                        maxlength="500"
                      />
                      <div class="reply-input-actions">
                        <el-button text @click="cancelReply">取消</el-button>
                        <el-button type="primary" @click="submitReply(level2Reply.id, level2Reply.user_id)" :disabled="!replyContent.trim()">
                          回复
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无评论" :image-size="100" />
    </el-card>

    <!-- 认领对话框 -->
    <el-dialog
      v-model="claimDialogVisible"
      title="申请认领"
      width="600px"
    >
      <el-form :model="claimForm" label-width="100px">
        <el-form-item label="认领说明">
          <el-input
            v-model="claimForm.description"
            type="textarea"
            :rows="4"
            placeholder="请描述物品的特征或提供认领证据..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="证据图片">
          <div class="claim-image-upload-container">
            <!-- 图片预览列表 -->
            <div class="claim-image-list" v-if="claimImageList.length > 0">
              <div
                v-for="(img, index) in claimImageList"
                :key="img.uid || index"
                class="claim-image-item-preview"
              >
                <img :src="img.preview" class="claim-thumbnail-image" />
                <div class="claim-image-overlay">
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    :icon="Delete"
                    @click="removeClaimImageByIndex(index)"
                    class="claim-delete-btn"
                  />
                </div>
                <div class="claim-image-index">{{ index + 1 }}</div>
              </div>
            </div>
            <el-upload
              v-if="claimImageList.length < 5"
              :auto-upload="false"
              :on-change="handleClaimImageChange"
              :show-file-list="false"
              :limit="5"
              multiple
              list-type="picture-card"
              accept="image/*"
              class="claim-image-uploader"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
            <div class="upload-tip">
              <p>最多上传5张图片，单张最大10MB，支持一次选择多张</p>
              <p>图片会自动压缩以节省空间</p>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelClaim">取消</el-button>
        <el-button
          type="primary"
          @click="submitClaim"
          :disabled="!claimForm.description.trim()"
        >
          提交申请
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  Picture,
  Location,
  Calendar,
  Clock,
  User,
  CopyDocument,
  Check,
  Delete,
  ChatDotRound,
  Star,
  Trophy,
  Connection,
  ChatLineRound,
  ArrowUp,
  ArrowDown,
  Plus,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import ReportDialog from "../components/ReportDialog.vue";
import request from "../utils/request";
import { isLoggedIn, getUser } from "../utils/auth";
import { absoluteUrl, previewList, previewListMultiple } from '../utils/request'
import imageCompression from 'browser-image-compression'

const route = useRoute();
const router = useRouter();
// 使用 computed 确保 itemId 会响应路由参数的变化
const itemId = computed(() => route.params.id);

const item = ref({});
const loading = ref(false);
const timeline = ref([]);
const shareVisible = ref(false);
const qrUrl = ref("");
const reportVisible = ref(false);
const currentMainImageIndex = ref(0);
const fullImageUrl = computed(() => item.value?.image_url ? absoluteUrl(item.value.image_url) : '')
const isFavorited = ref(false);
const matchedItems = ref([]);
const comments = ref([]);
const newComment = ref('');
const claimDialogVisible = ref(false);
const claimForm = ref({
  description: ''
});
const claimImageList = ref([]); // 认领证据图片列表（存储压缩后的文件）
const claims = ref([]); // 认领列表（仅发布者可见）
const replyingTo = ref(null);
const replyingToUserId = ref(null);  // 记录回复的目标用户ID
const replyContent = ref('');
const expandedReplies = ref(new Set());

// 获取所有图片URL（支持多张图片）
const imageUrls = computed(() => {
  if (item.value?.image_urls && Array.isArray(item.value.image_urls) && item.value.image_urls.length > 0) {
    return item.value.image_urls
  }
  // 向后兼容：如果没有 image_urls，使用 image_url
  if (item.value?.image_url) {
    return [item.value.image_url]
  }
  return []
})

// 预览图片列表
const previewImageUrls = computed(() => {
  return previewListMultiple(imageUrls.value)
})

// 切换主图（只改变显示的主图，不改变数组顺序）
const switchMainImage = (index) => {
  currentMainImageIndex.value = index
}

// 过滤时间线：只显示"发布"和"物品已找回"，并修改"物品已找回"的描述
const filteredTimeline = computed(() => {
  return timeline.value.filter(ev => {
    // 只保留"发布"和"物品已找回"相关的事件
    return ev.title === '发布' || ev.title === '物品已找回'
  }).map(ev => {
    // 修改"物品已找回"的描述
    if (ev.title === '物品已找回') {
      return {
        ...ev,
        description: item.value.category === 'lost' ? '恭喜！失物已找回！' : '恭喜！拾物已被找回！'
      }
    }
    return ev
  })
})

// 获取当前用户ID
const getCurrentUserId = () => {
  const user = getUser();
  return user?.id;
};

// 加载物品详情
const loadItemDetail = async () => {
  loading.value = true;
  const currentItemId = itemId.value; // 获取当前的 itemId
  try {
    item.value = await request.get(`/items/${currentItemId}`);
    console.log('[DEBUG] 加载的物品数据:', item.value)
    console.log('[DEBUG] image_url:', item.value.image_url)
    console.log('[DEBUG] image_urls:', item.value.image_urls)
    timeline.value = await request.get(`/items/${currentItemId}/timeline`);
    
    // 加载收藏状态
    if (isLoggedIn()) {
      try {
        const status = await request.get(`/items/${currentItemId}/favorite/status`);
        isFavorited.value = status.is_favorited;
      } catch (error) {
        console.error('加载收藏状态失败:', error);
      }
    }
    
    // 加载匹配推荐
    try {
      matchedItems.value = await request.get(`/items/${currentItemId}/matches`);
    } catch (error) {
      console.error('加载匹配推荐失败:', error);
    }
    
    // 加载认领列表（仅发布者可见）
    if (isLoggedIn() && item.value.user_id === getCurrentUserId()) {
      try {
        claims.value = await request.get(`/items/${currentItemId}/claims`);
      } catch (error) {
        // 如果不是发布者，会返回403，这是正常的
        if (error.response?.status !== 403) {
          console.error('加载认领列表失败:', error);
        }
        claims.value = [];
      }
    }
    
    // 加载评论
    try {
      const commentsData = await request.get(`/items/${currentItemId}/comments`);
      // 确保所有评论都有必要的字段
      comments.value = commentsData.map(comment => ({
        ...comment,
        user_avatar: comment.user_avatar || null,
        like_count: comment.like_count || 0,
        is_liked: comment.is_liked || false,
        replies_count: comment.replies_count || (comment.replies?.length || 0),
        replies: (comment.replies || []).map(reply => ({
          ...reply,
          user_avatar: reply.user_avatar || null,
          like_count: reply.like_count || 0,
          is_liked: reply.is_liked || false,
          level: reply.level !== undefined ? reply.level : 1,
          reply_to_username: reply.reply_to_username || null,
          reply_to_user_id: reply.reply_to_user_id || null,
          level2_replies: (reply.level2_replies || []).map(level2Reply => {
            // 确保二级回复有reply_to_username
            let replyToUsername = level2Reply.reply_to_username;
            if (!replyToUsername && level2Reply.reply_to_user_id) {
              // 如果后端没有返回，尝试从一级回复中获取
              if (level2Reply.reply_to_user_id === reply.user_id) {
                replyToUsername = reply.username;
              } else {
                // 尝试从其他回复中查找
                const targetUser = commentsData
                  .flatMap(c => c.replies || [])
                  .flatMap(r => [r, ...(r.level2_replies || [])])
                  .find(u => u.user_id === level2Reply.reply_to_user_id);
                if (targetUser) {
                  replyToUsername = targetUser.username;
                }
              }
            }
            return {
              ...level2Reply,
              user_avatar: level2Reply.user_avatar || null,
              like_count: level2Reply.like_count || 0,
              is_liked: level2Reply.is_liked || false,
              level: level2Reply.level !== undefined ? level2Reply.level : 2,
              reply_to_username: replyToUsername || null,
              reply_to_user_id: level2Reply.reply_to_user_id || null
            };
          })
        }))
      }));
    } catch (error) {
      console.error('加载评论失败:', error);
    }
  } catch (error) {
    console.error("加载详情失败:", error);
    ElMessage.error("加载失败");
  } finally {
    loading.value = false;
  }
};

// 联系发布者（新增）
const contactPublisher = async () => {
  try {
    if (isLoggedIn() && item.value.user_id === getCurrentUserId()) {
      ElMessage.warning("不能与自己创建会话");
      return;
    }
    // 获取或创建与发布者的会话
    const conversation = await request.post(
      `/conversations/${item.value.user_id}`
    );
    // 跳转到聊天页面
    router.push(`/chat/${conversation.id}`);
  } catch (error) {
    console.error("创建会话失败:", error);
    ElMessage.error("操作失败");
  }
};

// 复制电话
const copyPhone = async () => {
  const phone = item.value.contact_phone;
  
  // 优先使用现代剪贴板 API
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(phone);
      ElMessage.success("电话已复制到剪贴板");
      return;
    } catch (err) {
      console.warn('剪贴板 API 失败，尝试降级方案:', err);
    }
  }
  
  // 降级方案：使用传统的 execCommand 方法
  try {
    const textArea = document.createElement('textarea');
    textArea.value = phone;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    
    if (successful) {
      ElMessage.success("电话已复制到剪贴板");
    } else {
      ElMessage.error("复制失败，请手动复制");
    }
  } catch (err) {
    console.error('复制失败:', err);
    ElMessage.error("复制失败，请手动复制");
  }
};

// 标记为已解决
const markAsSolved = async () => {
  try {
    await ElMessageBox.confirm("确定要标记为已解决吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    await request.put(`/items/${itemId.value}`, { status: "closed" });
    ElMessage.success("已标记为已解决");
    await loadItemDetail();
  } catch (error) {
    if (error !== "cancel") {
      console.error("操作失败:", error);
    }
  }
};

// 删除物品
const deleteItem = async () => {
  try {
    await ElMessageBox.confirm(
      "确定要删除这条信息吗？删除后无法恢复。",
      "警告",
      {
        confirmButtonText: "确定删除",
        cancelButtonText: "取消",
        type: "error",
      }
    );

    await request.delete(`/items/${itemId.value}`);
    ElMessage.success("删除成功");
    router.push(`/list/${item.value.category}`);
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
    }
  }
};

// 返回列表
const goBack = () => {
  // 检查是否有返回信息（从列表页跳转过来）
  const from = route.query.from
  const category = route.query.category
  const page = route.query.page
  
  if (from === 'list' && category) {
    // 返回到列表页，并恢复页码和筛选条件
    router.push({
      path: `/list/${category}`,
      query: {
        page: page || 1,
        search: route.query.search || '',
        item_type: route.query.item_type || '',
        status: route.query.status || '',
        start_date: route.query.start_date || '',
        end_date: route.query.end_date || ''
      }
    })
  } else {
    // 默认返回上一页
    router.back()
  }
};

onMounted(() => {
  loadItemDetail();
});

// 监听路由参数变化，当 itemId 改变时重新加载数据
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      console.log('路由参数变化，从', oldId, '到', newId);
      // 重置状态
      item.value = {};
      comments.value = [];
      matchedItems.value = [];
      claims.value = [];
      isFavorited.value = false;
      // 使用 nextTick 确保路由完全更新后再加载数据
      nextTick(() => {
        loadItemDetail();
      });
    }
  },
  { immediate: false } // 不立即执行，只在路由变化时执行
);

const copyLink = async () => {
  const url = window.location.href;
  
  // 优先使用现代剪贴板 API
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(url);
      ElMessage.success("链接已复制到剪贴板");
      return;
    } catch (err) {
      console.warn('剪贴板 API 失败，尝试降级方案:', err);
    }
  }
  
  // 降级方案：使用传统的 execCommand 方法
  try {
    const textArea = document.createElement('textarea');
    textArea.value = url;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    
    if (successful) {
      ElMessage.success("链接已复制到剪贴板");
    } else {
      ElMessage.error("复制失败，请手动复制链接");
    }
  } catch (err) {
    console.error('复制失败:', err);
    ElMessage.error("复制失败，请手动复制链接");
  }
};

const openShare = () => {
  shareVisible.value = true;
  const url = window.location.href;
  qrUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=260x260&data=${encodeURIComponent(
    url
  )}`;
};

const viewPublisher = () => {
  if (item.value.user_id) {
    router.push(`/user/${item.value.user_id}/items`);
  }
};

const openReport = () => {
  reportVisible.value = true;
};
const onReported = () => {
  ElMessage.success("举报已提交");
};

// 收藏/取消收藏
const toggleFavorite = async () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  try {
    if (isFavorited.value) {
      await request.delete(`/items/${itemId.value}/favorite`);
      isFavorited.value = false;
      ElMessage.success('已取消收藏');
    } else {
      await request.post(`/items/${itemId.value}/favorite`);
      isFavorited.value = true;
      ElMessage.success('收藏成功');
    }
  } catch (error) {
    console.error('操作失败:', error);
    ElMessage.error('操作失败');
  }
};

// 提交评论
const submitComment = async () => {
  if (!newComment.value.trim()) {
    return;
  }
  
  try {
    const comment = await request.post(`/items/${itemId.value}/comments`, {
      content: newComment.value
    });
    // 确保返回的数据包含所有必要字段
    if (!comment.user_avatar) {
      comment.user_avatar = null;
    }
    if (comment.like_count === undefined) {
      comment.like_count = 0;
    }
    if (comment.is_liked === undefined) {
      comment.is_liked = false;
    }
    comments.value.unshift(comment);
    newComment.value = '';
    ElMessage.success('评论发表成功');
  } catch (error) {
    console.error('发表评论失败:', error);
    ElMessage.error('发表评论失败');
  }
};

// 格式化时间（相对时间）
const formatTime = (timeStr) => {
  if (!timeStr) return '';
  const time = new Date(timeStr);
  const now = new Date();
  const diff = now - time;
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const weeks = Math.floor(days / 7);
  const months = Math.floor(days / 30);
  const years = Math.floor(days / 365);
  
  if (years > 0) return `${years}年前`;
  if (months > 0) return `${months}个月前`;
  if (weeks > 0) return `${weeks}周前`;
  if (days > 0) return `${days}天前`;
  if (hours > 0) return `${hours}小时前`;
  if (minutes > 0) return `${minutes}分钟前`;
  return '刚刚';
};

// 获取一级回复（level=1的回复）
const getLevel1Replies = (replies) => {
  if (!replies) return [];
  return replies.filter(reply => (reply.level || 1) === 1);
};

// 切换回复输入框
const toggleReplyInput = (commentId, targetUserId = null) => {
  if (replyingTo.value === commentId) {
    replyingTo.value = null;
    replyingToUserId.value = null;
    replyContent.value = '';
  } else {
    replyingTo.value = commentId;
    replyingToUserId.value = targetUserId;
    replyContent.value = '';
  }
};

// 取消回复
const cancelReply = () => {
  replyingTo.value = null;
  replyingToUserId.value = null;
  replyContent.value = '';
};

// 提交回复
const submitReply = async (parentId, targetUserId = null) => {
  if (!replyContent.value.trim()) {
    return;
  }
  
  try {
    const currentUserId = getCurrentUserId();
    
    // 如果targetUserId为空，需要从parentId获取
    if (!targetUserId && parentId) {
      // 查找父评论（可能是一级评论、一级回复或二级回复）
      let parentComment = comments.value.find(c => c.id === parentId);
      if (parentComment) {
        // 父评论是一级评论
        targetUserId = parentComment.user_id;
      } else {
        // 可能是一级回复或二级回复，需要在一级评论的replies中查找
        for (const comment of comments.value) {
          if (comment.replies) {
            // 先在一级回复中查找
            const level1Reply = comment.replies.find(r => r.id === parentId);
            if (level1Reply) {
              targetUserId = level1Reply.user_id;
              break;
            }
            // 如果没找到，在二级回复中查找
            for (const level1Reply of comment.replies) {
              if (level1Reply.level2_replies) {
                const level2Reply = level1Reply.level2_replies.find(r => r.id === parentId);
                if (level2Reply) {
                  targetUserId = level2Reply.user_id;
                  break;
                }
              }
            }
            if (targetUserId) break;
          }
        }
      }
    }
    
    const reply = await request.post(`/items/${itemId.value}/comments`, {
      content: replyContent.value,
      parent_id: parentId,
      reply_to_user_id: targetUserId
    });
    
    // 确保返回的数据包含必要字段
    // 如果后端没有返回reply_to_username，尝试从现有数据中获取
    if (!reply.reply_to_username && reply.reply_to_user_id) {
      // 查找目标用户（可能在一级评论、一级回复或二级回复中）
      let targetUser = null;
      
      // 先在一级评论中查找
      const parentComment = comments.value.find(c => c.id === parentId);
      if (parentComment && reply.reply_to_user_id === parentComment.user_id) {
        targetUser = parentComment;
      } else {
        // 在一级回复和二级回复中查找
        for (const comment of comments.value) {
          if (comment.replies) {
            // 在一级回复中查找
            for (const level1Reply of comment.replies) {
              if (level1Reply.user_id === reply.reply_to_user_id) {
                targetUser = level1Reply;
                break;
              }
              // 在二级回复中查找
              if (level1Reply.level2_replies) {
                const level2Reply = level1Reply.level2_replies.find(r => r.user_id === reply.reply_to_user_id);
                if (level2Reply) {
                  targetUser = level2Reply;
                  break;
                }
              }
            }
            if (targetUser) break;
          }
        }
      }
      
      if (targetUser) {
        reply.reply_to_username = targetUser.username;
      }
    }
    if (reply.reply_to_username === undefined) {
      reply.reply_to_username = null;
    }
    if (reply.reply_to_user_id === undefined) {
      reply.reply_to_user_id = null;
    }
    if (reply.level === undefined) {
      // 判断是几级回复
      const parentComment = comments.value.find(c => c.id === parentId);
      if (parentComment) {
        reply.level = 1; // 一级回复（回复一级评论）
      } else {
        // 查找是否是一级回复或二级回复
        let found = false;
        for (const comment of comments.value) {
          if (comment.replies) {
            // 先在一级回复中查找
            const level1Reply = comment.replies.find(r => r.id === parentId);
            if (level1Reply) {
              reply.level = 2; // 二级回复（回复一级回复）
              found = true;
              break;
            }
            // 如果没找到，在二级回复中查找
            for (const level1Reply of comment.replies) {
              if (level1Reply.level2_replies) {
                const level2Reply = level1Reply.level2_replies.find(r => r.id === parentId);
                if (level2Reply) {
                  reply.level = 2; // 二级回复（回复二级回复）
                  found = true;
                  break;
                }
              }
            }
            if (found) break;
          }
        }
        // 如果都没找到，默认为二级回复
        if (!found) {
          reply.level = 2;
        }
      }
    }
    if (!reply.level2_replies) {
      reply.level2_replies = [];
    }
    
    // 更新评论列表
    // 找到父评论（可能是一级评论、一级回复或二级回复）
    let parentComment = comments.value.find(c => c.id === parentId);
    if (parentComment) {
      // 父评论是顶级评论，这是一级回复
      if (!parentComment.replies) {
        parentComment.replies = [];
      }
      parentComment.replies.push(reply);
      parentComment.replies_count = (parentComment.replies_count || 0) + 1;
    } else {
      // 如果没找到，可能是一级回复或二级回复，需要在一级评论的replies中查找
      let foundParent = null;
      let isLevel2Reply = false;
      
      for (const comment of comments.value) {
        if (comment.replies) {
          // 先在一级回复中查找
          const level1Reply = comment.replies.find(r => r.id === parentId);
          if (level1Reply) {
            // 找到了一级回复，这是二级回复
            foundParent = level1Reply;
            isLevel2Reply = true;
            break;
          }
          
          // 如果没找到，在二级回复中查找
          for (const level1Reply of comment.replies) {
            if (level1Reply.level2_replies) {
              const level2Reply = level1Reply.level2_replies.find(r => r.id === parentId);
              if (level2Reply) {
                // 找到了二级回复，新回复也应该添加到同一一级回复的level2_replies中
                foundParent = level1Reply;
                isLevel2Reply = true;
                break;
              }
            }
          }
          if (foundParent) break;
        }
      }
      
      if (foundParent) {
        // 这是二级回复
        if (!foundParent.level2_replies) {
          foundParent.level2_replies = [];
        }
        // 确保reply包含所有必要字段
        if (!reply.reply_to_username && reply.reply_to_user_id) {
          // 如果后端没有返回reply_to_username，尝试从现有数据中获取
          // 先尝试从一级回复中获取
          if (reply.reply_to_user_id === foundParent.user_id) {
            reply.reply_to_username = foundParent.username;
          } else {
            // 尝试从所有评论和回复中查找
            const targetUser = comments.value
              .flatMap(c => [c, ...(c.replies || []), ...(c.replies || []).flatMap(r => r.level2_replies || [])])
              .find(u => u && u.user_id === reply.reply_to_user_id);
            if (targetUser) {
              reply.reply_to_username = targetUser.username;
            }
          }
        }
        // 确保level为2
        reply.level = 2;
        foundParent.level2_replies.push(reply);
      } else {
        // 如果都没找到，重新加载评论列表
        console.warn('未找到父评论，重新加载评论列表');
        await loadItemDetail();
      }
    }
    
    replyContent.value = '';
    replyingTo.value = null;
    replyingToUserId.value = null;
    ElMessage.success('回复发表成功');
  } catch (error) {
    console.error('发表回复失败:', error);
    ElMessage.error('发表回复失败');
  }
};

// 切换回复显示/隐藏
const toggleReplies = (commentId) => {
  if (expandedReplies.value.has(commentId)) {
    expandedReplies.value.delete(commentId);
  } else {
    expandedReplies.value.add(commentId);
  }
};


// 编辑评论
const editComment = async (comment) => {
  try {
    const { value } = await ElMessageBox.prompt(
      '编辑评论',
      '评论内容',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: comment.content,
        inputType: 'textarea'
      }
    );
    
    const updated = await request.put(`/comments/${comment.id}`, {
      content: value
    });
    
    // 检查是否是顶级评论
    const topLevelIndex = comments.value.findIndex(c => c.id === comment.id);
    if (topLevelIndex !== -1) {
      // 更新顶级评论
      comments.value[topLevelIndex] = { ...comments.value[topLevelIndex], ...updated };
    } else {
      // 更新回复，需要在父评论的replies中更新（可能是一级或二级回复）
      for (const parentComment of comments.value) {
        if (parentComment.replies && parentComment.replies.length > 0) {
          // 先在一级回复中查找
          const replyIndex = parentComment.replies.findIndex(r => r.id === comment.id);
          if (replyIndex !== -1) {
            parentComment.replies[replyIndex] = { ...parentComment.replies[replyIndex], ...updated };
            break;
          }
          // 如果没找到，可能在二级回复中
          for (const level1Reply of parentComment.replies) {
            if (level1Reply.level2_replies && level1Reply.level2_replies.length > 0) {
              const level2Index = level1Reply.level2_replies.findIndex(r => r.id === comment.id);
              if (level2Index !== -1) {
                level1Reply.level2_replies[level2Index] = { ...level1Reply.level2_replies[level2Index], ...updated };
                break;
              }
            }
          }
        }
      }
    }
    
    ElMessage.success('评论已更新');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('编辑评论失败:', error);
      ElMessage.error('编辑失败');
    }
  }
};

// 删除评论
const deleteComment = async (commentId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await request.delete(`/comments/${commentId}`);
    
    // 检查是否是顶级评论
    const topLevelIndex = comments.value.findIndex(c => c.id === commentId);
    if (topLevelIndex !== -1) {
      // 删除顶级评论
      comments.value.splice(topLevelIndex, 1);
    } else {
      // 删除回复，需要从父评论的replies中移除（可能是一级或二级回复）
      let deleted = false;
      for (const comment of comments.value) {
        if (comment.replies && comment.replies.length > 0) {
          // 先在一级回复中查找
          const replyIndex = comment.replies.findIndex(r => r.id === commentId);
          if (replyIndex !== -1) {
            comment.replies.splice(replyIndex, 1);
            comment.replies_count = Math.max((comment.replies_count || 0) - 1, 0);
            deleted = true;
            break;
          }
          // 如果没找到，可能在二级回复中
          for (const level1Reply of comment.replies) {
            if (level1Reply.level2_replies && level1Reply.level2_replies.length > 0) {
              const level2Index = level1Reply.level2_replies.findIndex(r => r.id === commentId);
              if (level2Index !== -1) {
                level1Reply.level2_replies.splice(level2Index, 1);
                deleted = true;
                break;
              }
            }
          }
          if (deleted) break;
        }
      }
      
      // 如果删除失败，重新加载评论以确保数据一致性
      if (!deleted) {
        try {
          const commentsData = await request.get(`/items/${itemId.value}/comments`);
          comments.value = commentsData.map(comment => ({
            ...comment,
            user_avatar: comment.user_avatar || null,
            like_count: comment.like_count || 0,
            is_liked: comment.is_liked || false,
            replies_count: comment.replies_count || (comment.replies?.length || 0),
            replies: (comment.replies || []).map(reply => ({
              ...reply,
              user_avatar: reply.user_avatar || null,
              like_count: reply.like_count || 0,
              is_liked: reply.is_liked || false,
              level: reply.level || 1,
              reply_to_username: reply.reply_to_username || null,
              reply_to_user_id: reply.reply_to_user_id || null,
              level2_replies: (reply.level2_replies || []).map(level2Reply => ({
                ...level2Reply,
                user_avatar: level2Reply.user_avatar || null,
                like_count: level2Reply.like_count || 0,
                is_liked: level2Reply.is_liked || false,
                level: level2Reply.level || 2,
                reply_to_username: level2Reply.reply_to_username || null,
                reply_to_user_id: level2Reply.reply_to_user_id || null
              }))
            }))
          }));
        } catch (error) {
          console.error('重新加载评论失败:', error);
        }
      }
    }
    
    ElMessage.success('评论已删除');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除评论失败:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 打开认领对话框
const openClaimDialog = () => {
  if (!isLoggedIn()) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  claimDialogVisible.value = true;
  claimForm.value.description = '';
  claimImageList.value = [];
};

// 取消认领
const cancelClaim = () => {
  claimDialogVisible.value = false;
  claimForm.value.description = '';
  claimImageList.value = [];
};

// 处理认领图片上传（支持多选，参考发布信息功能的实现）
const handleClaimImageChange = async (file, fileList) => {
  // 检查是否已达到5张限制
  const currentCount = claimImageList.value.length;
  if (currentCount >= 5) {
    ElMessage.warning('最多只能上传5张图片，请先删除部分图片后再上传');
    return false;
  }

  const fileObj = file.raw || file;
  if (!fileObj || !(fileObj instanceof File)) {
    ElMessage.error('文件对象无效');
    return false;
  }

  const isImage = fileObj.type && fileObj.type.startsWith('image/');
  const originalSizeMB = fileObj.size / 1024 / 1024;

  if (!isImage) {
    ElMessage.error('只能上传图片文件！');
    return false;
  }
  
  // 检查原始文件大小（最大 10MB）
  if (originalSizeMB > 10) {
    ElMessage.error('图片大小不能超过10MB！');
    return false;
  }

  // 检查是否已存在相同文件（通过文件大小和最后修改时间）
  const isDuplicate = claimImageList.value.some(img => {
    if (img.originalFile) {
      return img.originalFile.size === fileObj.size && 
             img.originalFile.lastModified === fileObj.lastModified &&
             img.originalFile.name === fileObj.name;
    }
    return false;
  });

  if (isDuplicate) {
    ElMessage.warning('该图片已存在，请勿重复上传');
    return false;
  }

  try {
    // 压缩图片
    const options = {
      maxSizeMB: 2, // 压缩后最大 2MB
      maxWidthOrHeight: 1920, // 最大宽度或高度
      useWebWorker: true, // 使用 Web Worker 提高性能
      fileType: fileObj.type, // 保持原始格式
      initialQuality: 0.75 // 降低初始质量到75%以提高压缩速度
    };

    // 显示压缩提示
    const loadingMessage = ElMessage({
      message: '正在压缩图片...',
      type: 'info',
      duration: 0
    });

    const compressedBlob = await imageCompression(fileObj, options);
    
    // 将 Blob 转换为 File 对象
    const originalName = fileObj.name || `image_${Date.now()}.jpg`;
    const fileExtension = originalName.split('.').pop() || 'jpg';
    const fileName = originalName.replace(/\.[^/.]+$/, '') || 'image';
    const compressedFile = new File(
      [compressedBlob], 
      `${fileName}_compressed.${fileExtension}`, 
      { type: compressedBlob.type || fileObj.type }
    );
    
    // 关闭加载提示
    loadingMessage.close();

    const compressedSizeMB = compressedFile.size / 1024 / 1024;
    const compressionRatio = ((1 - compressedFile.size / fileObj.size) * 100).toFixed(1);
    
    // 如果压缩效果明显，显示提示
    if (compressionRatio > 20) {
      ElMessage.success(`图片已压缩：${originalSizeMB.toFixed(2)}MB → ${compressedSizeMB.toFixed(2)}MB (减少 ${compressionRatio}%)`);
    }

    // 检查总大小（5张 × 2MB = 10MB，留有余地设为 12MB）
    const currentTotalSize = claimImageList.value.reduce((sum, img) => sum + (img.file?.size || 0), 0);
    const newTotalSize = currentTotalSize + compressedFile.size;
    const maxTotalSize = 12 * 1024 * 1024; // 12MB（压缩后）

    if (newTotalSize > maxTotalSize) {
      const currentTotalMB = (currentTotalSize / 1024 / 1024).toFixed(2);
      ElMessage.error(`图片总大小不能超过12MB（压缩后）！当前已上传 ${currentTotalMB}MB，此图片 ${compressedSizeMB.toFixed(2)}MB`);
      return false;
    }

    // 创建预览
    const reader = new FileReader();
    reader.onload = (e) => {
      // 再次检查，防止在异步处理过程中超过限制
      if (claimImageList.value.length >= 5) {
        ElMessage.warning('最多只能上传5张图片');
        return;
      }
      
      // 再次检查是否重复
      const isStillDuplicate = claimImageList.value.some(img => {
        if (img.originalFile) {
          return img.originalFile.size === fileObj.size && 
                 img.originalFile.lastModified === fileObj.lastModified &&
                 img.originalFile.name === fileObj.name;
        }
        return false;
      });

      if (!isStillDuplicate) {
        claimImageList.value.push({
          uid: `claim-img-${Date.now()}-${Math.random()}`,
          file: compressedFile,
          preview: e.target.result,
          originalFile: fileObj,
          name: fileObj.name
        });
      }
    };
    reader.readAsDataURL(compressedFile);
    
    return true;
  } catch (error) {
    console.error('图片压缩失败:', error);
    ElMessage.error('图片压缩失败，请重试');
    return false;
  }
};

// 通过索引删除认领图片（更简单直接）
const removeClaimImageByIndex = (index) => {
  if (index >= 0 && index < claimImageList.value.length) {
    claimImageList.value.splice(index, 1);
  }
};

// 删除认领图片（兼容 el-upload 的 on-remove 事件，但现在不使用）
const removeClaimImage = (file, fileList) => {
  // 通过索引删除更可靠
  const index = claimImageList.value.findIndex(img => {
    if (img.originalFile && file.raw) {
      return img.originalFile === file.raw || 
             (img.originalFile.size === file.raw.size && 
              img.originalFile.lastModified === file.raw.lastModified &&
              img.originalFile.name === file.raw.name);
    }
    return false;
  });
  
  if (index !== -1) {
    claimImageList.value.splice(index, 1);
  }
};

// 提交认领申请
const submitClaim = async () => {
  try {
    const formData = new FormData();
    formData.append('description', claimForm.value.description);
    
    // 上传图片
    claimImageList.value.forEach((img) => {
      formData.append('images', img.file);
    });

    await request.post(`/items/${itemId.value}/claim`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    claimDialogVisible.value = false;
    claimForm.value.description = '';
    claimImageList.value = [];
    ElMessage.success('认领申请已提交，等待发布者确认');
  } catch (error) {
    console.error('提交认领失败:', error);
    ElMessage.error(error.response?.data?.message || '提交失败');
  }
};

// 批准认领
const approveClaim = async (claimId) => {
  try {
    await ElMessageBox.confirm('确定要批准这个认领申请吗？批准后物品状态将更新为"已解决"。', '确认批准', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await request.put(`/claims/${claimId}/approve`);
    ElMessage.success('认领申请已批准');
    
    // 重新加载认领列表和物品详情
    await loadItemDetail();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批准认领失败:', error);
      ElMessage.error(error.response?.data?.message || '操作失败');
    }
  }
};

// 拒绝认领
const rejectClaim = async (claimId) => {
  try {
    await ElMessageBox.confirm('确定要拒绝这个认领申请吗？', '确认拒绝', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await request.put(`/claims/${claimId}/reject`);
    ElMessage.success('认领申请已拒绝');
    
    // 重新加载认领列表
    await loadItemDetail();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('拒绝认领失败:', error);
      ElMessage.error(error.response?.data?.message || '操作失败');
    }
  }
};

// 联系申请认领者
const contactClaimant = async (claimantId) => {
  try {
    if (isLoggedIn() && claimantId === getCurrentUserId()) {
      ElMessage.warning("不能与自己创建会话");
      return;
    }
    // 获取或创建与认领者的会话
    const conversation = await request.post(
      `/conversations/${claimantId}`
    );
    // 跳转到聊天页面
    router.push(`/chat/${conversation.id}`);
  } catch (error) {
    console.error("创建会话失败:", error);
    ElMessage.error("操作失败");
  }
};

// 跳转到物品详情
const goToItem = (itemId) => {
  console.log('goToItem 被调用，itemId:', itemId);
  console.log('当前路由:', route.path);
  console.log('目标路由:', `/item/${itemId}`);
  
  if (!itemId) {
    console.error('itemId 为空');
    return;
  }
  
  const targetPath = `/item/${itemId}`;
  
  // 如果目标路由和当前路由相同，强制刷新
  if (route.path === targetPath) {
    console.log('目标路由与当前路由相同，强制刷新');
    router.go(0); // 刷新页面
    return;
  }
  
  // 使用 replace: false 确保是 push 而不是 replace
  router.push({
    path: targetPath
  }).then(() => {
    console.log('路由跳转成功');
  }).catch((error) => {
    console.error('路由跳转失败:', error);
  });
};
</script>

<style scoped>
.item-detail-container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.back-button {
  margin-bottom: 2rem;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.back-button:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.detail-card {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  padding: 2rem;
}

.image-section {
  width: 100%;
  border-radius: var(--border-radius);
  overflow: hidden;
  border: var(--border-width) solid var(--border-color);
}

.images-container {
  width: 100%;
}

.main-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--border-radius);
  margin-bottom: 1rem;
}

.thumbnail-list {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}

.thumbnail-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: var(--border-radius);
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.thumbnail-item:hover {
  border-color: var(--color-accent);
  transform: scale(1.05);
}

.thumbnail-item.active {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 0.8rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.thumbnail-item:hover .thumbnail-overlay {
  opacity: 1;
}

.item-image {
  width: 100%;
  height: 100%;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--color-primary);
  color: var(--text-secondary);
}

.info-section {
  padding: 20px 0;
}

.title-section {
  margin-bottom: 30px;
}

.title-section h2 {
  font-size: 2rem;
  font-weight: 900;
  margin: 0 0 15px 0;
  color: var(--color-text);
}

.tags {
  display: flex;
  gap: 10px;
}

.info-table {
  margin-bottom: 30px;
}

.description-section,
.contact-section {
  margin-bottom: 30px;
}

.timeline-section {
  margin-bottom: 30px;
}

.timeline-title {
  font-weight: 600;
}

.timeline-desc {
  color: var(--text-secondary);
}

.qr-box {
  display: flex;
  justify-content: center;
  align-items: center;
}

.description-section h3,
.contact-section h3 {
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 15px;
  color: var(--color-text);
}

.description-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
  background-color: var(--color-primary);
  padding: 1rem;
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}

.phone-number {
  font-size: 16px;
  font-weight: bold;
  color: #409eff;
}

.action-section {
  display: flex;
  gap: 15px;
  padding-top: 20px;
  border-top: var(--border-width) solid var(--border-color);
  flex-wrap: wrap;
}

.action-section .el-button {
  flex: 1;
  max-width: 200px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.action-section .el-button:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.action-section .el-button:active {
  transform: translateY(0) translateX(0);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .image-section {
    margin-bottom: 20px;
  }

  .action-section {
    flex-direction: column;
  }

  .action-section .el-button {
    max-width: 100%;
  }
}

/* 移动端适配（约 6.59 英寸 / 2412*1080） */
@media (max-width: 480px) {
  .item-detail-container {
    margin: 1rem auto;
    padding: 0 1rem;
  }

  .back-button {
    margin-bottom: 1rem;
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
  }

  .detail-card {
    padding: 1rem;
  }

  .title-section h2 {
    font-size: 1.4rem;
  }

  .tags {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .action-section {
    gap: 0.75rem;
  }

  .action-section .el-button {
    width: 100%;
    max-width: none;
  }

  .thumbnail-item {
    width: 60px;
    height: 60px;
  }

  .claim-actions {
    flex-wrap: wrap;
  }

  .claim-actions .el-button {
    flex: 1;
    min-width: 80px;
  }
}

@media (max-width: 414px) {
  .item-detail-container {
    padding: 0 0.75rem;
  }

  .title-section h2 {
    font-size: 1.25rem;
  }
}

/* 对话框中的输入框样式 */
.item-detail-container :deep(.el-dialog) {
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.item-detail-container :deep(.el-dialog .el-button) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.item-detail-container :deep(.el-dialog .el-button--primary) {
  background: var(--color-accent);
  color: white !important;
}

.item-detail-container :deep(.el-dialog .el-button:hover) {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

/* 移动端对话框全宽 */
@media (max-width: 480px) {
  .item-detail-container :deep(.el-dialog) {
    width: 95% !important;
    max-width: 95%;
    margin: 0 auto;
  }

  .item-detail-container :deep(.el-dialog__body) {
    padding: 1rem;
  }
}

/* 匹配推荐卡片 */
.matches-card {
  margin-top: 2rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.2rem;
}

.match-item-wrapper {
  cursor: pointer;
  width: 100%;
}

.match-item-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  margin-bottom: 1rem;
  width: 100%;
}

.match-item-card:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.match-item-image-wrapper {
  width: 100%;
  height: 150px;
  overflow: hidden;
  border-radius: var(--border-radius);
  pointer-events: none;
}

.match-item-image {
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.match-item-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  border-radius: var(--border-radius);
  color: var(--text-secondary);
  pointer-events: none;
}

.match-item-info {
  padding: 1rem 0;
  pointer-events: none;
}

.match-item-info h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
}

.match-item-location {
  margin: 0.5rem 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

/* 评论卡片 */
.comments-card {
  margin-top: 2rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

/* 评论输入区域 */
.comment-input-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: var(--border-width) solid var(--border-color);
}

.comment-input-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.comment-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.comment-submit-btn {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  font-weight: 600;
}

.comment-login-tip {
  margin-bottom: 2rem;
  padding: 1rem;
  text-align: center;
  background: var(--color-primary);
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}

/* 评论列表 */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.comment-item {
  padding: 1rem 0;
  border-bottom: 1px solid var(--border-color);
}

.comment-item:last-child {
  border-bottom: none;
}

/* 一级评论头部 */
.comment-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.comment-author {
  font-weight: 700;
  color: var(--color-text);
  font-size: 1rem;
}

.comment-time {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* 评论内容 */
.comment-content {
  color: var(--color-text);
  line-height: 1.6;
  margin-bottom: 0.5rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 操作按钮 */
.comment-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

/* 回复输入框 */
.reply-input-box {
  margin-top: 0.75rem;
  margin-left: 1rem;
}

.reply-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

/* 回复区域 */
.replies-section {
  margin-top: 1rem;
  padding-left: 1rem;
  border-left: 2px solid var(--border-color);
}

.toggle-replies-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: var(--border-radius);
  color: var(--color-accent);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 0.5rem;
}

.toggle-replies-btn:hover {
  background: var(--color-primary);
}

.replies-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

/* 回复项 */
.reply-item {
  padding: 0.5rem 0;
}

.reply-item.level-1 {
  padding-left: 0.5rem;
}

.reply-item.level-2 {
  padding-left: 1rem;
  margin-top: 0.5rem;
}

/* 回复行（一行显示：用户名：回复内容 时间） */
.reply-line {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.25rem;
}

.reply-author {
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.95rem;
}

.reply-to-text {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin: 0 0.25rem;
}

.reply-target {
  color: var(--color-accent);
  font-weight: 600;
}

.reply-separator {
  color: var(--color-text);
  font-size: 0.95rem;
}

.reply-content {
  color: var(--color-text);
  font-size: 0.95rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.reply-time {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-left: 0.5rem;
}

/* 回复操作按钮 */
.reply-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
  margin-left: 0.5rem;
}

/* 二级回复列表 */
.level-2-replies {
  margin-top: 0.5rem;
  padding-left: 0.5rem;
}

/* 认领列表区域 */
.claims-card {
  margin-top: 2rem;
  background: var(--color-card);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.claims-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.claim-item {
  padding: 1rem;
  background: var(--color-primary);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.claim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.claim-user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.claim-username {
  font-weight: 700;
  color: var(--color-text);
  font-size: 1rem;
}

.claim-time {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.claim-description {
  color: var(--color-text);
  line-height: 1.6;
  margin-bottom: 0.75rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 0.75rem;
  background: var(--color-card);
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}

.claim-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

/* 认领证据图片 */
.claim-images {
  margin-top: 0.75rem;
}

.claim-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.5rem;
}

.claim-image-item {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.claim-image-item:hover {
  transform: scale(1.05);
}

/* 认领图片上传 */
.claim-image-upload-container {
  width: 100%;
}

.claim-image-uploader :deep(.el-upload) {
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
  background: var(--color-primary);
}

.claim-image-uploader :deep(.el-upload:hover) {
  border-color: var(--color-accent);
  transform: translateY(-2px) translateX(-2px);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
}

.upload-tip {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.upload-tip p {
  margin: 0.25rem 0;
}

/* 认领图片预览列表 */
.claim-image-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.claim-image-item-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--border-radius);
  overflow: hidden;
  border: var(--border-width) solid var(--border-color);
  box-shadow: var(--shadow-offset) var(--shadow-offset) 0px 0px var(--shadow-color);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.claim-image-item-preview:hover {
  transform: translateY(-2px) translateX(-2px);
  box-shadow: calc(var(--shadow-offset) + 2px) calc(var(--shadow-offset) + 2px) 0px 0px var(--shadow-color);
}

.claim-thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.claim-image-overlay {
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
  transition: opacity 0.2s ease;
}

.claim-image-item-preview:hover .claim-image-overlay {
  opacity: 1;
}

.claim-delete-btn {
  background: rgba(255, 255, 255, 0.9);
  border: var(--border-width) solid var(--border-color);
}

.claim-image-index {
  position: absolute;
  top: 0.25rem;
  left: 0.25rem;
  background: var(--color-card);
  color: var(--color-text);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.5rem;
  border-radius: var(--border-radius);
  border: var(--border-width) solid var(--border-color);
}
</style>
