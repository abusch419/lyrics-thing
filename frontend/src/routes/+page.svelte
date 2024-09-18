<script lang="ts">
	import { onMount } from 'svelte';
	import * as Urls from '../lib/Urls.shared';

	// Function to fetch the hello message from the backend
	async function fetchHelloWorld() {
		try {
			const response = await fetch(`${Urls.apiRoot()}/`);
			if (response.ok) {
				const data = await response.json();
				console.log(data.message); // Should print "world" to the console
			} else {
				console.error('Failed to fetch the hello message.');
			}
		} catch (error) {
			console.error('Error fetching hello message:', error);
		}
	}

	// Fetch the hello message when the component is loaded
	onMount(() => {
		fetchHelloWorld();
	});
</script>

<h1>Welcome to SvelteKit</h1>
<p>
	Visit <a href="https://kit.svelte.dev">kit.svelte.dev</a> to read the documentation
</p>
