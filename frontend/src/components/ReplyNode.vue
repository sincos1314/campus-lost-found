<template>
  <div class="reply-item level-2">
    <div class="reply-line">
      <span class="reply-author">{{ reply.username }}</span>
      <template v-if="reply.reply_to_user_id && reply.reply_to_user_id !== reply.user_id">
        <span class="reply-to-text">
          回复
          <span class="reply-target">{{ reply.reply_to_username || '用户' }}</span>
        </span>
      </template>
      <span class="reply-separator">：</span>
      <span class="reply-content">{{ reply.content }}</span>
      <span class="reply-time"> {{ formatTime(reply.created_at) }}</span>
    </div>
    <div class="reply-actions">
      <el-button
        text
        size="small"
        @click="toggleLike(reply)"
        :class="{ 'is-liked': reply.is_liked }"
        class="like-btn"
      >
        <svg class="like-icon" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
          <path d="M2 20h2V8H2v12zm20-11a2 2 0 0 0-2-2h-6.31l.95-4.57.03-.32a1.49 1.49 0 0 0-.44-1.06L13.17 0 6.59 6.59A1.98 1.98 0 0 0 6 8v10a2 2 0 0 0 2 2h9a2 2 0 0 0 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73V9z"/>
        </svg>
        <span v-if="reply.like_count > 0" class="like-count">{{ reply.like_count }}</span>
      </el-button>
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
    <!-- 递归：子回复（支持多层回复链） -->
    <div v-if="reply.level2_replies && reply.level2_replies.length > 0" class="level-2-replies">
      <ReplyNode
        v-for="r in reply.level2_replies"
        :key="r.id"
        :reply="r"
      />
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue';

defineOptions({ name: 'ReplyNode' });

const props = defineProps({
  reply: { type: Object, required: true }
});

const replyingTo = inject('replyingTo');
const replyContent = inject('replyContent');
const formatTime = inject('formatTime');
const toggleReplyInput = inject('toggleReplyInput');
const submitReply = inject('submitReply');
const cancelReply = inject('cancelReply');
const getCurrentUserId = inject('getCurrentUserId');
const isLoggedIn = inject('isLoggedIn');
const editComment = inject('editComment');
const deleteComment = inject('deleteComment');
const toggleLike = inject('toggleLike');
</script>

<style scoped>
/* 与 ItemDetail 评论区保持一致，确保时间与内容有分隔（scoped 下子组件不会继承父样式） */
.reply-line {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.25rem;
}

.reply-author {
  font-weight: 600;
  color: var(--color-text, #333);
  font-size: 0.95rem;
}

.reply-to-text {
  color: var(--text-secondary, #666);
  font-size: 0.95rem;
  margin: 0 0.25rem;
}

.reply-target {
  color: var(--color-accent, #409eff);
  font-weight: 600;
}

.reply-separator {
  color: var(--color-text, #333);
  font-size: 0.95rem;
}

.reply-content {
  color: var(--color-text, #333);
  font-size: 0.95rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.reply-time {
  font-size: 0.85rem;
  color: var(--text-secondary, #666);
  margin-left: 0.5rem;
}

.reply-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
  margin-left: 0.5rem;
}

.like-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--text-secondary, #909399);
  transition: color 0.2s;
}

.like-btn:hover {
  color: var(--color-accent, #409eff) !important;
}

.like-btn.is-liked {
  color: var(--color-accent, #409eff) !important;
}

.like-icon {
  vertical-align: middle;
}

.like-count {
  font-size: 0.85rem;
  margin-left: 0.1rem;
}

.level-2-replies {
  margin-top: 0.5rem;
  padding-left: 0.5rem;
}
</style>
