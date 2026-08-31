import argparse
import json

from dotenv import load_dotenv

from .service import run_scheduled_if_due, run_seo_cycle


def main():
    load_dotenv('.env.local')
    load_dotenv()
    parser = argparse.ArgumentParser(description='Run the NovaBrief SEO Studio monitoring cycle.')
    parser.add_argument('--trigger', default='scheduled', choices=['scheduled', 'manual', 'deployment'])
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    result = run_scheduled_if_due() if args.trigger == 'scheduled' and not args.force else run_seo_cycle(trigger_type=args.trigger, force=args.force)
    print(json.dumps({key: value for key, value in result.items() if key != 'audit'}, default=str))
    return 0 if result['status'] in {'completed', 'disabled', 'already_running', 'not_due'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
