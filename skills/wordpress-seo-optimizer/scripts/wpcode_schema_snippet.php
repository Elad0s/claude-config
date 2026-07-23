<?php
/**
 * Per-page JSON-LD for a WordPress + Yoast + Elementor stack, via WPCode.
 *
 * Paste WITHOUT the opening "<?php" tag into a WPCode "PHP Snippet"
 * (Auto Insert / Run Everywhere / Active). It hooks wp_head so it fires on
 * every front-end template — including CPT single templates where Elementor's
 * elementor_head hook does NOT fire. See references/schema-injection.md (B).
 *
 * Emits: Service on the service CPT, BlogPosting on posts, Article on the
 * project CPT. provider/author/publisher all link to <base>/#localbusiness so
 * the page schema joins the global LocalBusiness node from the Elementor snippet.
 *
 * EDIT: $base, the post-type list in is_singular(), and the $counties list.
 */
add_action( 'wp_head', function () {

	// Which singular templates get schema, and edit the $base + areaServed below.
	if ( ! is_singular( array( 'service', 'post', 'project' ) ) ) {
		return;
	}
	$post = get_queried_object();
	if ( ! $post instanceof WP_Post ) {
		return;
	}

	$base = 'https://example.com';   // production domain, no trailing slash
	$id    = $post->ID;
	$url   = str_replace( home_url(), $base, get_permalink( $id ) ); // stays correct after domain move
	$title = wp_strip_all_tags( get_the_title( $id ) );
	$logo  = $base . '/wp-content/uploads/logo.webp';

	// Description: Yoast meta description -> excerpt -> trimmed content.
	$desc = trim( (string) get_post_meta( $id, '_yoast_wpseo_metadesc', true ) );
	if ( '' === $desc ) {
		$desc = has_excerpt( $id )
			? get_the_excerpt( $id )
			: wp_trim_words( wp_strip_all_tags( $post->post_content ), 40 );
	}

	// Featured image (omitted gracefully if none).
	$img = '';
	if ( has_post_thumbnail( $id ) ) {
		$img = wp_get_attachment_image_url( get_post_thumbnail_id( $id ), 'full' );
		if ( $img ) {
			$img = str_replace( home_url(), $base, $img );
		}
	}

	$publisher = array(
		'@type' => 'Organization',
		'@id'   => $base . '/#localbusiness',
		'name'  => get_bloginfo( 'name' ),
		'logo'  => array( '@type' => 'ImageObject', 'url' => $logo ),
	);
	$author = array(
		'@type' => 'Organization',
		'@id'   => $base . '/#localbusiness',
		'name'  => get_bloginfo( 'name' ),
	);

	$node = array();

	if ( 'service' === $post->post_type ) {
		$counties = array( 'Middlesex County, MA', 'Essex County, MA' ); // EDIT
		$areas = array();
		foreach ( $counties as $county ) {
			$areas[] = array( '@type' => 'AdministrativeArea', 'name' => $county );
		}
		$node = array(
			'@context' => 'https://schema.org', '@type' => 'Service',
			'@id' => $url . '#service', 'name' => $title, 'serviceType' => $title,
			'url' => $url, 'description' => $desc,
			'provider' => array( '@type' => 'LocalBusiness', '@id' => $base . '/#localbusiness',
			                     'name' => get_bloginfo( 'name' ) ),
			'areaServed' => $areas,
		);
	} elseif ( 'post' === $post->post_type ) {
		$node = array(
			'@context' => 'https://schema.org', '@type' => 'BlogPosting',
			'@id' => $url . '#article', 'headline' => $title, 'name' => $title,
			'url' => $url, 'mainEntityOfPage' => $url,
			'datePublished' => get_the_date( 'c', $id ), 'dateModified' => get_the_modified_date( 'c', $id ),
			'description' => $desc, 'inLanguage' => 'en-US',
			'author' => $author, 'publisher' => $publisher,
		);
	} elseif ( 'project' === $post->post_type ) {
		$node = array(
			'@context' => 'https://schema.org', '@type' => 'Article',
			'@id' => $url . '#project', 'headline' => $title, 'name' => $title,
			'url' => $url, 'mainEntityOfPage' => $url,
			'datePublished' => get_the_date( 'c', $id ), 'dateModified' => get_the_modified_date( 'c', $id ),
			'description' => $desc, 'inLanguage' => 'en-US',
			'author' => $author, 'publisher' => $publisher,
		);
	}

	if ( $img && ! empty( $node ) ) {
		$node['image'] = $img;
	}
	if ( ! empty( $node ) ) {
		echo "\n" . '<script type="application/ld+json">'
			. wp_json_encode( $node, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE )
			. '</script>' . "\n";
	}
}, 20 );
