import unittest

from news_relevance import assess_news_relevance, filter_relevant_news


class NewsRelevanceTests(unittest.TestCase):
    def test_accepts_major_company_ai_product_news(self):
        article = {
            'title': 'NVIDIA launches a new GPU platform for AI researchers',
            'summary': 'The semiconductor platform targets university labs and developers.',
            'url': 'https://example.com/nvidia-ai-chip',
        }
        result = assess_news_relevance(article)
        self.assertTrue(result['is_relevant'])
        self.assertIn('NVIDIA', result['companies'])
        self.assertIn('Artificial intelligence', result['topics'])

    def test_accepts_student_opportunities(self):
        article = {
            'title': 'Google opens global student developer scholarship',
            'summary': 'The program helps university students learn cloud computing.',
            'url': 'https://example.com/google-students',
        }
        self.assertTrue(assess_news_relevance(article)['is_relevant'])

    def test_accepts_programming_and_open_source_news(self):
        article = {
            'title': 'Python releases a major update for software developers',
            'summary': 'The programming language adds developer tools and performance improvements.',
            'source': 'Linux Foundation',
            'url': 'https://example.com/python-release',
        }
        result = assess_news_relevance(article)
        self.assertTrue(result['is_relevant'])
        self.assertIn('Programming and software', result['topics'])

    def test_accepts_useful_science_and_future_technology(self):
        article = {
            'title': 'University researchers announce battery technology breakthrough',
            'summary': 'The clean energy technology could improve electric vehicles.',
            'source': 'Nature',
            'url': 'https://example.com/battery-research',
        }
        result = assess_news_relevance(article)
        self.assertTrue(result['is_relevant'])
        self.assertIn('Science and future technology', result['topics'])

    def test_accepts_digital_skills_and_certification_news(self):
        article = {
            'title': 'Free cloud certification program opens for university students',
            'summary': 'The technology training covers developer tools and digital skills.',
            'url': 'https://example.com/student-certification',
        }
        result = assess_news_relevance(article)
        self.assertTrue(result['is_relevant'])
        self.assertIn('Digital skills and education', result['topics'])

    def test_rejects_generic_entertainment_and_sports(self):
        stories = [
            {'title': 'Celebrity red carpet fashion trend goes viral', 'summary': '', 'url': 'https://example.com/1'},
            {'title': 'Football match ends with dramatic late score', 'summary': '', 'url': 'https://example.com/2'},
        ]
        self.assertEqual(filter_relevant_news(stories), [])

    def test_rejects_finance_only_company_story(self):
        article = {
            'title': 'NVIDIA stock price rises after analyst upgrade',
            'summary': 'A new price target lifted investor sentiment.',
            'url': 'https://example.com/nvidia-stock',
        }
        self.assertFalse(assess_news_relevance(article)['is_relevant'])

    def test_rejects_big_tech_shopping_deals(self):
        article = {
            'title': "Amazon sale is live: shop deals on Apple devices",
            'summary': 'The best deals include discounted TVs and accessories.',
            'url': 'https://example.com/amazon-sale',
        }
        self.assertFalse(assess_news_relevance(article)['is_relevant'])
        live_example = {
            'title': 'Amazon offers early savings on Mac Mini, plus record low on AirTag',
            'summary': 'A shopping guide for discounted Apple devices.',
            'url': 'https://example.com/discounts',
        }
        self.assertFalse(assess_news_relevance(live_example)['is_relevant'])

    def test_rejects_ambiguous_company_words(self):
        stories = [
            {'title': 'New discoveries in the Amazon rainforest', 'summary': 'Wildlife research.', 'url': 'https://example.com/forest'},
            {'title': 'Easy apple pie recipe for students', 'summary': 'A quick dessert.', 'url': 'https://example.com/pie'},
        ]
        self.assertEqual(filter_relevant_news(stories), [])

    def test_keeps_finance_story_when_it_contains_a_real_tech_event(self):
        article = {
            'title': 'NVIDIA stock moves after company unveils a new AI chip',
            'summary': 'The GPU platform was announced for machine learning developers.',
            'url': 'https://example.com/nvidia-launch',
        }
        self.assertTrue(assess_news_relevance(article)['is_relevant'])

    def test_deduplicates_and_ranks_stronger_story_first(self):
        stories = [
            {'title': 'Amazon announces a new device', 'summary': '', 'url': 'https://example.com/a'},
            {
                'title': 'Google DeepMind releases multimodal AI model for researchers',
                'summary': 'The artificial intelligence research release includes developer tools.',
                'url': 'https://example.com/b',
            },
            {'title': 'Duplicate', 'summary': 'Google technology', 'url': 'https://example.com/a'},
        ]
        results = filter_relevant_news(stories)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['url'], 'https://example.com/b')

    def test_diversifies_companies_when_enough_stories_exist(self):
        stories = []
        for index in range(5):
            stories.append({
                'title': f'OpenAI releases AI model update {index}',
                'summary': 'A new artificial intelligence model for developers.',
                'url': f'https://example.com/openai-{index}',
            })
        stories.extend([
            {'title': 'NVIDIA launches new AI chip', 'summary': 'A GPU for researchers.', 'url': 'https://example.com/nvidia'},
            {'title': 'Google releases cloud AI platform', 'summary': 'Developer tools are included.', 'url': 'https://example.com/google'},
            {'title': 'Amazon AWS announces AI service', 'summary': 'A cloud platform for students.', 'url': 'https://example.com/aws'},
        ])
        results = filter_relevant_news(stories, limit=5)
        companies = {company for item in results for company in item['companies']}
        self.assertTrue({'OpenAI', 'NVIDIA', 'Google', 'Amazon'}.issubset(companies))

    def test_diversifies_technology_topics(self):
        stories = [
            {
                'title': f'OpenAI releases AI model update {index}',
                'summary': 'A new artificial intelligence model for developers.',
                'url': f'https://example.com/ai-{index}',
            }
            for index in range(5)
        ]
        stories.extend([
            {'title': 'Python programming language releases major update', 'summary': 'Software developers get new tools.', 'url': 'https://example.com/python'},
            {'title': 'Critical cybersecurity vulnerability receives security update', 'summary': 'Developers should patch systems.', 'url': 'https://example.com/security'},
            {'title': 'University announces battery technology breakthrough', 'summary': 'Clean energy research advances.', 'url': 'https://example.com/battery'},
        ])
        results = filter_relevant_news(stories, limit=5)
        topics = {topic for item in results for topic in item['news_topics']}
        self.assertTrue({'Artificial intelligence', 'Programming and software', 'Cybersecurity', 'Science and future technology'}.issubset(topics))

    def test_reputable_reporting_ranks_above_low_signal_opinion(self):
        stories = [
            {
                'title': 'OpenAI AI incident draws online reaction',
                'summary': 'An opinion about artificial intelligence companies.',
                'source': 'Example Substack',
                'url': 'https://example.com/opinion',
            },
            {
                'title': 'NVIDIA releases new AI chip for researchers',
                'summary': 'The GPU platform supports machine learning workloads.',
                'source': 'Reuters',
                'url': 'https://example.com/reporting',
            },
        ]
        results = filter_relevant_news(stories)
        self.assertEqual(results[0]['url'], 'https://example.com/reporting')

    def test_removes_same_story_reported_by_multiple_outlets(self):
        stories = [
            {
                'title': 'Sony and Warner Music sue Anthropic over songs used in AI training - Reuters',
                'summary': 'The labels filed a lawsuit about artificial intelligence training.',
                'source': 'Reuters',
                'url': 'https://example.com/reuters-story',
            },
            {
                'title': 'Sony, Warner Music sue Anthropic, saying it pirated songs to train its AI - Al Jazeera',
                'summary': 'Music labels brought a case over artificial intelligence.',
                'source': 'Al Jazeera',
                'url': 'https://example.com/aljazeera-story',
            },
        ]
        results = filter_relevant_news(stories)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['source'], 'Reuters')


if __name__ == '__main__':
    unittest.main()
