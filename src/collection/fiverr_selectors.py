"""Named Fiverr DOM selectors used by collection modules."""

# Session verification
LOGGED_IN_INDICATOR = "[data-testid='user-menu-button']"
LOGGED_IN_FALLBACK = ".nav-link.user-actions"

# Search results page
SEARCH_RESULT_COUNT = "[data-testid='results-count'], .results-count, h1.listings-perseus"
GIG_CARD_CONTAINER = "[data-testid='gig-card-layout'], .gig-card-layout"
GIG_CARD_TITLE = "[data-testid='gig-title'], .gig-title"
GIG_CARD_SELLER_NAME = "[data-testid='seller-name'], .seller-name"
GIG_CARD_SELLER_LEVEL = "[data-testid='seller-level-badge'], .seller-level-badge"
GIG_CARD_RATING = "[data-testid='rating-count'], .rating-count-number"
GIG_CARD_REVIEW_COUNT = "[data-testid='rating-count-number'], .reviews-count"
GIG_CARD_PRICE = "[data-testid='starting-price'], .gig-price"
GIG_CARD_DELIVERY = "[data-testid='delivery-time'], .delivery-time"
GIG_CARD_LINK = "a[data-testid='gig-link'], a.gig-link"
GIG_CARD_SPONSORED = "[data-testid='promoted-badge'], .promoted-badge"
GIG_CARD_QUEUE = "[data-testid='orders-queue'], .orders-queue"
PAGINATION_NEXT = "[data-testid='pagination-next'], .pagination-next"

# Gig detail page
GIG_DETAIL_TITLE = "h1.title"
GIG_DETAIL_DESCRIPTION = "[data-testid='description'], .description, .gig-description"
GIG_DETAIL_PACKAGES = "[data-testid='package-header'], .package-content"
GIG_DETAIL_PACKAGE_PRICE = "[data-testid='package-price'], .price"
GIG_DETAIL_PACKAGE_ITEMS = "[data-testid='package-includes'] li, .package-items li"
GIG_DETAIL_DELIVERY = "[data-testid='delivery-time-value'], .delivery-days"
GIG_DETAIL_REVISIONS = "[data-testid='revisions-value'], .revisions"
GIG_DETAIL_EXTRAS = "[data-testid='gig-extra'], .gig-extra-service"
GIG_DETAIL_TAGS = "[data-testid='tag'], .gig-tags a, .tags-wrapper a"
GIG_DETAIL_FAQ_ITEMS = "[data-testid='faq-item'], .faq-item"
GIG_DETAIL_FAQ_QUESTION = "[data-testid='faq-question'], .question"
GIG_DETAIL_FAQ_ANSWER = "[data-testid='faq-answer'], .answer"
GIG_DETAIL_VIDEO = "[data-testid='gig-video'], video, .gig-video-player"
GIG_DETAIL_PORTFOLIO = "[data-testid='portfolio-item'], .portfolio-gallery-item"
GIG_DETAIL_REVIEW_COUNT = "[data-testid='review-count'], .reviews-header .count"
GIG_DETAIL_RATING = "[data-testid='rating-value'], .main-ratings-score"
GIG_DETAIL_REVIEW_ITEMS = "[data-testid='review-item'], .review-item"
GIG_DETAIL_THUMBNAIL = "img[data-testid='gig-thumbnail'], img.gallery-image-container"
GIG_DETAIL_ORDERS_QUEUE = "[data-testid='orders-in-queue'], .orders-in-queue"
GIG_DETAIL_READ_MORE = "[data-testid='read-more'], .read-more-btn, button.read-more"

# Seller profile page
# UNVERIFIED — requires live DOM validation before first real run
SELLER_LEVEL_BADGE = "[data-testid='seller-level-badge'], [data-testid='seller-level'], .seller-level-badge, .seller-level"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_MEMBER_SINCE = "[data-testid='seller-member-since'], [data-testid='member-since'], .member-since"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_RESPONSE_TIME = "[data-testid='seller-response-time'], [data-testid='response-time'], .response-time"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_RESPONSE_RATE = "[data-testid='seller-response-rate'], [data-testid='response-rate'], .response-rate"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_LANGUAGES = "[data-testid='seller-language-item'], [data-testid='language-item'], .languages li, .language-list li"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_BIO = "[data-testid='seller-bio'], [data-testid='seller-description'], .seller-overview p, .seller-bio"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_TOTAL_REVIEWS = "[data-testid='seller-total-reviews'], [data-testid='seller-review-count'], .total-reviews"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_TOTAL_GIGS = "[data-testid='seller-total-gigs'], [data-testid='gig-count'], .gigs-count"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_GIG_TITLE = "[data-testid='seller-gig-title'], [data-testid='gig-title'], .gig-list .title, .gig-title"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_PORTFOLIO_ITEM = "[data-testid='seller-portfolio-item'], [data-testid='portfolio-item'], .portfolio-item"
# UNVERIFIED — requires live DOM validation before first real run
SELLER_BADGE = "[data-testid='seller-badge-item'], [data-testid='badge-item'], .badge-card"

# Backward-compatible aliases for legacy tests/callers.
SELLER_REVIEW_COUNT = SELLER_TOTAL_REVIEWS
SELLER_GIG_COUNT = SELLER_TOTAL_GIGS
SELLER_GIG_TITLES = SELLER_GIG_TITLE
SELLER_PORTFOLIO_ITEMS = SELLER_PORTFOLIO_ITEM
SELLER_BADGES = SELLER_BADGE
