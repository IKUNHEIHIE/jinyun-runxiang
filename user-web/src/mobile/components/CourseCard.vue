<script setup lang="ts">
import { mediaUrl } from "../api";
import { designIcon } from "../design";
defineProps<{
  course: {
    id: number;
    title: string;
    cover_url?: string;
    duration_minutes?: number;
    subtitle?: string;
    progress_percent?: number;
    rating?: number;
    chapter_count?: number;
  };
  compact?: boolean;
}>();
</script>
<template>
  <RouterLink
    :to="'/courses/' + course.id"
    class="course-card"
    :class="{ compact, 'corner-card': compact }"
    :aria-label="'学习：' + course.title"
  >
    <img
      v-if="course.cover_url"
      class="course-cover"
      :src="mediaUrl(course.cover_url)"
      :alt="course.title"
      loading="lazy"
    />
    <div v-else class="course-cover image-empty">非遗</div>
    <div class="course-info">
      <h3>{{ course.title }}</h3>
      <div v-if="compact" class="course-meta">
        <span>小课</span><span>{{ course.duration_minutes || 0 }}分钟</span>
      </div>
      <div
        class="course-rating"
        :aria-label="
          course.rating == null
            ? '暂无评分'
            : '评分 ' + course.rating.toFixed(1) + ' / 5'
        "
      >
        <span class="rating-stars" aria-hidden="true"
          ><span v-for="star in 5" :key="star" class="rating-star"
            ><img
              :src="
                compact
                  ? designIcon('home', '5:02314')
                  : designIcon('layer-40-32392', '5:05555')
              "
              alt="" /><span
              :style="{
                width:
                  Math.max(0, Math.min(1, (course.rating || 0) - star + 1)) *
                    100 +
                  '%',
              }"
              ><img
                :src="
                  compact
                    ? designIcon('home', '5:02314')
                    : designIcon('layer-40-32392', '5:05555')
                "
                alt="" /></span></span
        ></span>
        <span>{{
          course.rating == null ? "暂无评分" : course.rating.toFixed(1)
        }}</span>
      </div>
      <div v-if="!compact" class="course-bottom">
        <span>{{ course.chapter_count || 0 }}课时</span>
        <div class="progress-track">
          <i
            :style="{
              width:
                Math.min(100, Math.max(0, course.progress_percent || 0)) + '%',
            }"
          />
        </div>
        <span>{{ course.progress_percent || 0 }}%</span>
      </div>
    </div>
  </RouterLink>
</template>
<style scoped>
.course-card:not(.compact) {
  border: 1px solid #ebe3d5;
  border-radius: 16px;
  background: #fffdf8;
  overflow: hidden;
  color: #5c4033;
}
.course-card:not(.compact) .course-cover {
  width: 100%;
  height: auto;
  aspect-ratio: 159.5 / 130;
  border-radius: 0;
}
.course-card:not(.compact) .course-info {
  padding: 12px;
}
.course-card:not(.compact) h3 {
  font-size: 13px;
  font-weight: 500;
  line-height: 18px;
  height: 38px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.course-rating {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 15px;
  margin-top: 6px;
  color: #a89880;
  font-size: 10px;
  line-height: 15px;
}
.rating-stars {
  display: flex;
  gap: 4px;
}
.rating-star {
  position: relative;
  width: 12px;
  height: 12px;
}
.rating-star > img {
  opacity: 0.2;
}
.rating-star img {
  position: absolute;
  width: 12px;
  height: 12px;
  max-width: none;
}
.rating-star > span {
  position: absolute;
  height: 12px;
  overflow: hidden;
}
.course-bottom {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0 0;
  font-size: 11px;
  height: 16px;
  line-height: 16px;
  color: #a89880;
}
.course-bottom > span {
  flex-shrink: 0;
}
.course-bottom > span:last-child {
  font-size: 10px;
}
.course-bottom .progress-track {
  flex: 1;
  height: 6px;
  border: 0;
  background: rgba(232, 220, 192, 0.5);
}
.course-bottom .progress-track i {
  background: #c4a265;
}
.compact .course-info h3 {
  font-size: 15px;
  line-height: 22.5px;
  font-weight: 600;
  white-space: nowrap;
}
.compact .course-meta {
  gap: 0;
  font-size: 10px;
  line-height: 15px;
  color: #6c0a0a;
}
.compact .course-meta span {
  padding: 0;
  border-radius: 0;
  background: none;
}
.compact .course-cover {
  border: 1px solid #e8d9a8;
}
.compact:after {
  background-size:
    14px 1.5px,
    1.5px 14px,
    14px 1.5px,
    1.5px 14px,
    14px 1.5px,
    1.5px 14px,
    14px 1.5px,
    1.5px 14px;
}
.compact .course-rating {
  position: absolute;
  top: 33px;
  left: 0;
  margin: 0;
  gap: 6px;
  font-size: 9px;
}
.compact .rating-stars {
  gap: 4px;
}
.compact .rating-star,
.compact .rating-star img {
  width: 11px;
  height: 11px;
}
.compact .rating-star > span {
  height: 11px;
}
</style>
