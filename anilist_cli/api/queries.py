"""GraphQL queries and mutations for the AniList API."""

GET_VIEWER = """
query {
  Viewer {
    id
    name
    about
    siteUrl
    createdAt
    updatedAt
    avatar {
      medium
      large
    }
    bannerImage
  }
}
"""

SEARCH_MEDIA = """
query (
  $search: String,
  $type: MediaType,
  $genre: String,
  $status: MediaStatus,
  $format: MediaFormat,
  $sort: [MediaSort],
  $page: Int,
  $perPage: Int,
  $season: MediaSeason,
  $seasonYear: Int,
  $isAdult: Boolean
) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
    }
    media(
      search: $search,
      type: $type,
      genre: $genre,
      status: $status,
      format: $format,
      sort: $sort,
      season: $season,
      seasonYear: $seasonYear,
      isAdult: $isAdult
    ) {
      id
      type
      format
      status
      season
      seasonYear
      episodes
      chapters
      volumes
      duration
      source
      countryOfOrigin
      isAdult
      siteUrl
      popularity
      favourites
      meanScore
      genres
      title {
        romaji
        english
        native
      }
      coverImage {
        medium
        large
        extraLarge
        color
      }
      bannerImage
      tags {
        name
        rank
      }
      studios(isMain: true) {
        nodes {
          name
        }
      }
      startDate {
        year
        month
        day
      }
    }
  }
}
"""

GET_TRENDING = """
query ($type: MediaType!, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
    }
    media(type: $type, sort: TRENDING_DESC, isAdult: false) {
      id
      type
      format
      status
      season
      seasonYear
      episodes
      chapters
      duration
      popularity
      favourites
      meanScore
      genres
      title {
        romaji
        english
        native
      }
      coverImage {
        medium
        large
        extraLarge
        color
      }
      bannerImage
      studios(isMain: true) {
        nodes {
          name
        }
      }
      startDate {
        year
      }
    }
  }
}
"""

GET_POPULAR = """
query ($type: MediaType!, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      hasNextPage
      currentPage
    }
    media(type: $type, sort: POPULARITY_DESC, isAdult: false) {
      id
      type
      format
      status
      season
      seasonYear
      episodes
      chapters
      duration
      popularity
      meanScore
      genres
      title {
        romaji
        english
        native
      }
      coverImage {
        medium
        large
        extraLarge
        color
      }
      startDate {
        year
      }
    }
  }
}
"""

GET_SEASONAL = """
query ($season: MediaSeason!, $seasonYear: Int!, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      hasNextPage
      currentPage
    }
    media(
      type: ANIME,
      season: $season,
      seasonYear: $seasonYear,
      sort: POPULARITY_DESC,
      isAdult: false
    ) {
      id
      type
      format
      status
      season
      seasonYear
      episodes
      duration
      popularity
      meanScore
      genres
      title {
        romaji
        english
        native
      }
      coverImage {
        medium
        large
        extraLarge
        color
      }
      bannerImage
      studios(isMain: true) {
        nodes {
          name
        }
      }
    }
  }
}
"""

GET_MEDIA_DETAILS = """
query ($id: Int!) {
  Media(id: $id) {
    id
    type
    format
    status
    season
    seasonYear
    episodes
    chapters
    volumes
    duration
    source
    countryOfOrigin
    isAdult
    siteUrl
    popularity
    favourites
    meanScore
    genres
    description(asHtml: false)
    title {
      romaji
      english
      native
    }
    coverImage {
      medium
      large
      extraLarge
      color
    }
    bannerImage
    tags {
      name
      rank
      isMediaSpoiler
    }
    studios(isMain: true) {
      nodes {
        name
        siteUrl
      }
    }
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    characters(sort: [ROLE, RELEVANCE], perPage: 12) {
      edges {
        role
        node {
          id
          name {
            full
            native
          }
          image {
            medium
            large
          }
        }
      }
    }
    relations {
      edges {
        relationType(version: 2)
        node {
          id
          type
          format
          title {
            romaji
            english
          }
          coverImage {
            medium
          }
          status
        }
      }
    }
    mediaListEntry {
      id
      status
      progress
      score
      notes
    }
    nextAiringEpisode {
      airingAt
      episode
      timeUntilAiring
    }
  }
}
"""

GET_MEDIA_LIST_COLLECTION = """
query ($userId: Int!, $type: MediaType!) {
  MediaListCollection(userId: $userId, type: $type) {
    lists {
      name
      status
      isCustomList
      entries {
        id
        status
        progress
        score
        notes
        repeat
        private
        updatedAt
        media {
          id
          type
          format
          status
          episodes
          chapters
          volumes
          meanScore
          genres
          title {
            romaji
            english
            native
          }
          coverImage {
            medium
            large
            extraLarge
          }
          startDate {
            year
          }
        }
      }
    }
  }
}
"""

SAVE_MEDIA_LIST_ENTRY = """
mutation (
  $id: Int,
  $mediaId: Int,
  $status: MediaListStatus,
  $score: Float,
  $progress: Int,
  $progressVolumes: Int,
  $repeat: Int,
  $notes: String,
  $private: Boolean
) {
  SaveMediaListEntry(
    id: $id,
    mediaId: $mediaId,
    status: $status,
    score: $score,
    progress: $progress,
    progressVolumes: $progressVolumes,
    repeat: $repeat,
    notes: $notes,
    private: $private
  ) {
    id
    status
    progress
    progressVolumes
    score
    repeat
    notes
    private
    updatedAt
    media {
      id
      title {
        romaji
        english
      }
      type
      episodes
      chapters
    }
  }
}
"""

DELETE_MEDIA_LIST_ENTRY = """
mutation ($id: Int!) {
  DeleteMediaListEntry(id: $id) {
    deleted
  }
}
"""

GET_USER_STATISTICS = """
query ($userId: Int!) {
  User(id: $userId) {
    id
    name
    statistics {
      anime {
        count
        meanScore
        minutesWatched
        episodesWatched
        statuses {
          status
          count
          meanScore
          minutesWatched
        }
        genres(sort: COUNT_DESC, limit: 10) {
          genre
          count
          meanScore
          minutesWatched
        }
        tags(sort: COUNT_DESC, limit: 10) {
          tag {
            name
          }
          count
          meanScore
          minutesWatched
        }
      }
      manga {
        count
        meanScore
        chaptersRead
        volumesRead
        statuses {
          status
          count
          meanScore
          chaptersRead
        }
        genres(sort: COUNT_DESC, limit: 10) {
          genre
          count
          meanScore
          chaptersRead
        }
        tags(sort: COUNT_DESC, limit: 10) {
          tag {
            name
          }
          count
          meanScore
          chaptersRead
        }
      }
    }
  }
}
"""
